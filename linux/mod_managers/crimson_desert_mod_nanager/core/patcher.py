"""Format 2 (raw byte) and format 3 (semantic) patch mods on .pabgb files."""

import json
import re
import sys
from pathlib import Path

from .display   import _ok, _info, _warn, _err, GREEN, YELLOW, CYAN, RESET, BOLD
from .installer import _installed_versions, _install_status, _version_gt
from .overlay   import write_overlay
from .packager  import _get_cdumm_iteminfo_parser, _get_dmm, extract_file, find_game_path, COMP_NONE
from .sources   import list_mods

_parse_fn:     object = None
_serial_fn:    object = None
_apply_fn:     object = None
_normalize_fn: object = None
_parser_tried: bool   = False


# ── Format 2 — patches raw-byte ───────────────────────────────────────────────

def _apply_f2(body: bytearray, changes: list[dict]) -> int:
    applied = 0
    for ch in changes:
        off  = ch.get('offset', 0)
        orig = bytes.fromhex(ch.get('original', ''))
        new  = bytes.fromhex(ch.get('patched', ''))
        if len(orig) != len(new):
            _warn(f"  offset {off}: size mismatch, skipped"); continue
        if body[off:off + len(orig)] != orig:
            _warn(f"  offset {off}: original bytes not found (already patched?)"); continue
        body[off:off + len(new)] = new
        applied += 1
    return applied


def apply_format2(patch_data: dict, game_dir: Path) -> dict[str, bytes]:
    """Returns {game_file: patched_bytes} for each patches[] entry."""
    result = {}
    for patch in patch_data.get('patches', []):
        game_file = patch.get('game_file', '')
        hint      = int(patch['source_group']) if patch.get('source_group') else None
        raw       = extract_file(game_dir, game_file, overlay_hint=hint)
        if raw is None:
            _err(f"  Cannot extract '{game_file}'"); continue
        body     = bytearray(raw)
        changes  = patch.get('changes', [])
        applied  = _apply_f2(body, changes)
        total    = len(changes)
        if applied == total:
            _info(f"  {game_file}: {applied}/{total} patches")
            canonical = find_game_path(game_dir, game_file) or game_file
            result[canonical] = bytes(body)
        else:
            skipped = total - applied
            pct     = skipped * 100 // total if total else 0
            _err(f"  {game_file}: {applied}/{total} patches"
                 f"  ({pct}% skipped) — mod incompatible with this game version, installation cancelled")
    return result


# ── Format 3 — patches sémantiques (iteminfo) ─────────────────────────────────

def _load_parser():
    global _parse_fn, _serial_fn, _apply_fn, _normalize_fn, _parser_tried
    if _parse_fn:
        return _parse_fn, _serial_fn
    if _parser_tried:
        raise RuntimeError("iteminfo parser unavailable (both dmm_parser and CDUMM Python failed)")
    _parser_tried = True

    # CDUMM Python parser takes priority for iteminfo: always up to date for new
    # game builds (e.g. field unk_flag_b23693656 added in 1.11), without depending
    # on recompiling the dmm_parser binary.
    cdumm = _get_cdumm_iteminfo_parser()
    if cdumm is not None:
        _parse_fn  = cdumm.parse_iteminfo_from_bytes
        _serial_fn = cdumm.serialize_iteminfo

    # dmm_parser binary: needed for apply_intents / normalize_target_name (other tables)
    # and as iteminfo fallback if CDUMM Python is unavailable.
    dmm = _get_dmm()
    if dmm is not None:
        if _parse_fn is None:
            try:
                _parse_fn  = dmm.parse_iteminfo_from_bytes
                _serial_fn = dmm.serialize_iteminfo
            except AttributeError as e:
                raise RuntimeError(f"incompatible dmm_parser: {e}") from e
        _apply_fn     = getattr(dmm, 'apply_intents', None)
        _normalize_fn = getattr(dmm, 'normalize_target_name', None)

    if _parse_fn is None:
        raise RuntimeError(
            "iteminfo parser unavailable — check dependances/ or cdumm_src in config.json"
        )
    return _parse_fn, _serial_fn


def _field_candidates(name: str) -> list[str]:
    candidates = [name, f'_{name}']
    if '_' in name:
        camel = re.sub(r'_([a-z])', lambda m: m.group(1).upper(), name)
        if camel != name:
            candidates += [camel, f'_{camel}']
    return candidates


def _apply_f3_iteminfo(body: bytes, intents: list[dict]) -> bytes:
    parse, serial = _load_parser()
    items   = parse(body)
    by_name = {}
    by_key  = {}
    for item in items:
        for k in ('_string_key', 'string_key', '_name', 'name'):
            if item.get(k):
                by_name[str(item[k])] = item; break
        for k in ('_key', 'key', '_itemKey', 'itemKey'):
            if k in item:
                by_key[int(item[k])] = item; break

    applied = 0
    for intent in intents:
        item = (by_name.get(str(intent.get('entry', '')))
                or by_key.get(int(intent.get('key', 0))))
        if item is None:
            _warn(f"  '{intent.get('entry')}' not found"); continue
        fk = next((c for c in _field_candidates(str(intent.get('field', ''))) if c in item), None)
        if fk is None:
            _warn(f"  field '{intent.get('field')}' not found"); continue
        item[fk] = intent.get('new')
        applied += 1

    _info(f"  {applied}/{len(intents)} intents applied")
    return serial(items)


def apply_format3(patch_data: dict, game_dir: Path) -> dict[str, bytes]:
    """Returns {game_file: patched_bytes} for each target."""
    result = {}
    if 'targets' in patch_data:
        pairs = [(t['file'], t.get('intents', [])) for t in patch_data['targets']]
    else:
        pairs = [(patch_data.get('target', ''), patch_data.get('intents', []))]
    for target, intents in pairs:
        table     = target.split('/')[-1].lower().replace('.pabgb', '')
        game_file = target if '/' in target else f"gamedata/{target}"
        canonical = find_game_path(game_dir, game_file) or game_file
        raw       = extract_file(game_dir, canonical)
        if raw is None:
            _err(f"  Cannot extract '{canonical}'"); continue
        if table == 'iteminfo':
            try:
                result[canonical] = _apply_f3_iteminfo(raw, intents)
            except (RuntimeError, NotImplementedError) as e:
                _err(str(e))
        else:
            try:
                _load_parser()
                if not _apply_fn:
                    _err(f"  dmm_parser.apply_intents not available"); continue
                resolved = (
                    (_normalize_fn(table)          if _normalize_fn else None)
                    or (_normalize_fn(table + 'info') if _normalize_fn else None)
                    or table
                )
                if _normalize_fn and _normalize_fn(resolved) is None:
                    _err(f"  Table '{table}' not supported by dmm_parser"); continue
                canonical_gh = canonical.replace('.pabgb', '.pabgh')
                raw_gh = extract_file(game_dir, canonical_gh)
                patched = _apply_fn(resolved, raw, raw_gh, intents)
                if isinstance(patched, dict):
                    new_pabgb = patched.get('body') or patched.get('pabgb') or patched.get(canonical)
                    new_pabgh = patched.get('pabgh') or patched.get(canonical_gh)
                    if new_pabgb is not None:
                        result[canonical] = bytes(new_pabgb)
                    if new_pabgh is not None:
                        result[canonical_gh] = bytes(new_pabgh)
                    if canonical not in result:
                        _err(f"  apply_intents: body (body/pabgb) missing from result")
                elif isinstance(patched, (tuple, list)) and len(patched) >= 2:
                    result[canonical] = bytes(patched[0])
                    if patched[1] is not None:
                        result[canonical_gh] = bytes(patched[1])
                elif isinstance(patched, (bytes, bytearray)):
                    result[canonical] = bytes(patched)
                else:
                    _err(f"  apply_intents: unexpected return for '{table}' ({type(patched).__name__})")
                if canonical in result:
                    _info(f"  {table}: {len(intents)} intent(s) applied")
            except (RuntimeError, NotImplementedError, TypeError) as e:
                _err(str(e))
    return result


# ── Installation ──────────────────────────────────────────────────────────────

def install_patch(patch_file: Path, game_dir: Path) -> bool:
    """Installs a patch (format 2 or 3) from a JSON file."""
    try:
        data = json.loads(patch_file.read_text(encoding='utf-8-sig'))
    except Exception as e:
        _err(f"Cannot read {patch_file.name}: {e}"); return False

    fmt     = int(data.get('format', 0))
    patches = data.get('patches', [])
    if fmt == 0 and patches and isinstance(patches[0], dict) and 'changes' in patches[0]:
        fmt = 2

    modinfo  = data.get('modinfo', {})
    mod_name = modinfo.get('title') or data.get('name', patch_file.stem)
    mod_id   = re.sub(r'[^\w\-.]', '_', patch_file.stem)
    version  = str(modinfo.get('version') or data.get('version', '?'))

    _info(f"Installing '{mod_name}' (format {fmt}) ...")

    if fmt == 2:
        file_map = apply_format2(data, game_dir)
    elif fmt == 3:
        file_map = apply_format3(data, game_dir)
    else:
        _err(f"Unrecognized format {fmt}"); return False

    if not file_map:
        _err("No files patched — installation cancelled"); return False

    entries  = []
    payloads = []
    for game_file, data_bytes in file_map.items():
        parts = game_file.replace('\\', '/').split('/')
        entries.append({
            'dir_path':  '/'.join(parts[:-1]),
            'filename':  parts[-1],
            'comp_size': len(data_bytes),
            'orig_size': len(data_bytes),
            'flags':     COMP_NONE,
        })
        payloads.append(data_bytes)
        _info(f"  {game_file}  ({len(data_bytes):,} B)")

    return write_overlay(entries, payloads, mod_name, mod_id, version, game_dir, 'patcher')


# ── Commandes ─────────────────────────────────────────────────────────────────

def cmd_update(patch_dir: Path, game_dir: Path, yes: bool = False) -> int:
    """Installs only patches whose available version > installed version."""
    patches   = [m for m in list_mods(patch_dir) if m.get('_patch_format')]
    installed = _installed_versions(game_dir, patch_dir)
    updates   = []
    for m in patches:
        s = _install_status(m, installed)
        if s[0] == 'update' and _version_gt(s[2], s[1]):
            updates.append((m, s[1], s[2]))

    if not updates:
        return 0

    print(f"\n  {BOLD}Patch mods updates — {len(updates)} patch(es){RESET}\n")
    for m, old_ver, new_ver in updates:
        print(f"  {YELLOW}↑{RESET}  {BOLD}{m.get('title', m['_path'].name)}{RESET}  v{old_ver} → v{new_ver}")
    print()

    if not yes:
        try:
            rep = input("  Update? [y/N]  ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(); _info("Cancelled."); return 0
        if rep not in ('y', 'yes'):
            _info("Cancelled."); return 0

    ok = sum(install_patch(m['_path'], game_dir) for m, _, _ in updates)
    _ok(f"{ok}/{len(updates)} patch(es) updated")
    return ok


def cmd_dry_run(patch_dir: Path, game_dir: Path, force: bool = False, yes: bool = False) -> None:
    """Displays available patches in mods/patch/ and offers to install them."""
    patches = [m for m in list_mods(patch_dir) if m.get('_patch_format')]
    if not patches:
        return

    installed = _installed_versions(game_dir, patch_dir)
    statuses  = [_install_status(m, installed) for m in patches]
    n_ok      = sum(1 for s in statuses if s[0] == 'up_to_date')

    print(f"\n  {BOLD}Patch mods — {len(patches)} available{RESET}\n")
    for i, m in enumerate(patches):
        s   = statuses[i]
        tag = (f"  {CYAN}[✓ v{s[1]}]{RESET}"           if s[0] == 'up_to_date' else
               f"  {YELLOW}[↑ v{s[1]}→v{s[2]}]{RESET}" if s[0] == 'update'     else
               f"  {GREEN}[new]{RESET}")
        print(f"  [p{i+1}] {BOLD}{m.get('title', m['_path'].name)}{RESET}"
              f"  (format {m.get('_patch_format')}){tag}")

    if n_ok and not force:
        print(f"\n  {CYAN}{n_ok} already up to date — skipped{RESET}")

    todo = [i for i, s in enumerate(statuses) if force or s[0] != 'up_to_date']
    if not todo:
        print(f"\n  {GREEN}Everything is up to date.{RESET}\n"); return

    print()
    if yes:
        sel_idx = todo
    else:
        try:
            rep = input(
                f"  Patches to install (e.g.: {' '.join(f'p{i+1}' for i in todo)})"
                f", 'all', empty = skip: "
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print(); return
        if not rep:
            return
        if rep.lower() in ('all', 'y', 'yes'):
            sel_idx = todo
        else:
            try:
                sel_idx = [int(x.lstrip('p')) - 1 for x in rep.split() if x.lstrip('p').isdigit()]
            except (ValueError, IndexError):
                _err(f"Invalid input: {rep!r}"); return

    ok = sum(install_patch(patches[i]['_path'], game_dir) for i in sel_idx)
    _ok(f"{ok}/{len(sel_idx)} patch(es) installed")
