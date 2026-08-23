"""Browser mods: PAZ/PAMT overlay installation, uninstall, status."""

import re
import shutil
from pathlib import Path

from .display  import _ok, _info, _warn, _err, GREEN, YELLOW, RESET, BOLD, CYAN
from .crypto   import needs_encryption
from .overlay  import write_overlay
from .packager import prepare_file
from .sources  import collect_mod_files, list_mods
from .state    import load_state, save_state


def install_mod(mod: dict, game_dir: Path,
                files: list | None = None) -> bool:
    """Installs a browser mod by creating an NNNN/ overlay with 0.paz and 0.pamt."""
    mod_id   = mod.get('id', mod['_path'].name)
    mod_name = mod.get('title', mod_id)
    _info(f"Installing '{mod_name}' ...")

    if files is None:
        files = collect_mod_files(mod)
    if not files:
        _err(f"No files found for '{mod_name}'"); return False

    entries  = []
    payloads = []
    for dir_path, filename, src in files:
        try:
            payload, comp_size, orig_size, comp_type = prepare_file(src)
        except Exception as e:
            _warn(f"  {filename}: error → {e}, skipped"); continue
        encrypted = needs_encryption(filename)
        flags     = (0x30 | comp_type) if encrypted else comp_type
        _info(f"  {filename}  ({orig_size} → {comp_size} B, type {comp_type}"
              f"{'+enc' if encrypted else ''})")
        entries.append({'dir_path': dir_path, 'filename': filename,
                        'comp_size': comp_size, 'orig_size': orig_size, 'flags': flags})
        payloads.append(payload)

    if not entries:
        _err("No valid files"); return False

    return write_overlay(entries, payloads, mod_name, mod_id,
                         str(mod.get('version', '?')), game_dir, 'installer')


def uninstall_mod(mod_id: str, game_dir: Path, yes: bool = False) -> bool:
    """Removes the overlay of a browser mod by its id."""
    state = load_state(game_dir)
    found = next(
        (f for f, info in state['overlays'].items()
         if f == mod_id
         or info.get('mod_id') == mod_id
         or info.get('content') == mod_id),
        None,
    )
    if not found:
        _err(f"Mod '{mod_id}' not found"); return False

    name = state['overlays'][found].get('content', mod_id)
    if not yes:
        try:
            rep = input(f"  Uninstall '{name}' ({found}/) ? [y/N]  ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(); _info("Cancelled."); return False
        if rep not in ('y', 'yes'):
            _info("Cancelled."); return False

    overlay_dir = game_dir / found
    if overlay_dir.is_dir():
        shutil.rmtree(overlay_dir)
    del state['overlays'][found]
    save_state(game_dir, state)
    _ok(f"'{name}' uninstalled ({found}/ removed)")
    return True


def _installed_versions(game_dir: Path, mods_dir: Path | None = None) -> dict[str, str]:
    """Returns {mod_id: version} for all installed overlays."""
    source_ver = {}
    if mods_dir:
        for m in list_mods(mods_dir):
            source_ver[m.get('id', m['_path'].name)] = str(m.get('version', '?'))

    result = {}
    for folder, info in load_state(game_dir).get('overlays', {}).items():
        mid = info.get('mod_id')
        if not mid:
            continue
        ver = str(info.get('version', ''))
        if not ver or ver == '?':
            marker = game_dir / folder / f'.mod_{mid}'
            if marker.is_file():
                for line in marker.read_text(errors='ignore').splitlines():
                    if line.startswith('Version:'):
                        ver = line.split(':', 1)[1].strip(); break
        if (not ver or ver == '?') and mid in source_ver:
            ver = source_ver[mid]
        result[mid] = ver or '?'
    return result


def _install_status(m: dict, installed: dict[str, str]) -> tuple:
    """Returns ('new',) | ('up_to_date', ver) | ('update', old, new)."""
    mid      = m.get('id', m['_path'].name)
    inst_ver = installed.get(mid)
    if inst_ver is None:
        return ('new',)
    curr_ver = str(m.get('version', '?'))
    return ('up_to_date', inst_ver) if inst_ver == curr_ver else ('update', inst_ver, curr_ver)


def _version_gt(new_ver: str, old_ver: str) -> bool:
    """True if new_ver > old_ver — numeric segment comparison (1.9 < 1.10)."""
    def parts(v: str) -> list:
        return [int(x) if x.isdigit() else x for x in re.split(r'[.\-_]', str(v).strip())]
    try:
        return parts(new_ver) > parts(old_ver)
    except TypeError:
        return str(new_ver) != str(old_ver)


def cmd_update(mods_dir: Path, game_dir: Path, yes: bool = False) -> int:
    """Installs only browser mods whose available version > installed version."""
    mods      = [m for m in list_mods(mods_dir) if m.get('enabled', True) and not m.get('_patch_format')]
    installed = _installed_versions(game_dir, mods_dir)

    updates = []
    for m in mods:
        s = _install_status(m, installed)
        if s[0] == 'update' and _version_gt(s[2], s[1]):
            updates.append((m, s[1], s[2]))

    if not updates:
        return 0

    print(f"\n  {BOLD}Available updates — {len(updates)} mod(s){RESET}\n")
    for m, old_ver, new_ver in updates:
        title = m.get('title', m.get('id', m['_path'].name))
        print(f"  {YELLOW}↑{RESET}  {BOLD}{title}{RESET}  v{old_ver} → v{new_ver}")
    print()

    if not yes:
        try:
            rep = input("  Update? [y/N]  ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(); _info("Cancelled."); return 0
        if rep not in ('y', 'yes'):
            _info("Cancelled."); return 0

    ok = sum(install_mod(m, game_dir) for m, _, _ in updates)
    _ok(f"{ok}/{len(updates)} mod(s) updated")
    return ok


def cmd_dry_run(mods_dir: Path, game_dir: Path, force: bool = False, yes: bool = False) -> None:
    """Displays available browser mods, detects conflicts, and installs."""
    mods = sorted(
        [m for m in list_mods(mods_dir) if m.get('enabled', True) and not m.get('_patch_format')],
        key=lambda m: (m.get('priority', 0), m['_path'].name),
    )
    if not mods:
        _info("No enabled browser mods in mods/"); return

    installed  = _installed_versions(game_dir, mods_dir)
    statuses   = [_install_status(m, installed) for m in mods]
    mod_files  = [collect_mod_files(m) for m in mods]

    owners: dict[str, list[int]] = {}
    for i, files in enumerate(mod_files):
        for dp, fn, _ in files:
            owners.setdefault(f"{dp}/{fn}" if dp else fn, []).append(i)
    conflicts  = {k: v for k, v in owners.items() if len(v) > 1}
    conflicted = {i for idxs in conflicts.values() for i in idxs}

    n_ok = sum(1 for s in statuses if s[0] == 'up_to_date')
    print(f"\n  {BOLD}Browser mods — {len(mods)} enabled mod(s){RESET}\n")
    for i, m in enumerate(mods):
        title = m.get('title', m.get('id', m['_path'].name))
        nf    = len(mod_files[i])
        s     = statuses[i]
        tag   = (f"  {CYAN}[✓ v{s[1]}]{RESET}"           if s[0] == 'up_to_date' else
                 f"  {YELLOW}[↑ v{s[1]}→v{s[2]}]{RESET}" if s[0] == 'update'     else
                 f"  {GREEN}[new]{RESET}")
        if i in conflicted:
            my = [k for k, idxs in conflicts.items() if i in idxs]
            print(f"  [{i+1}] {BOLD}{title}{RESET}  ({nf} files)"
                  f"  {YELLOW}⚠ {len(my)} conflict(s){RESET}{tag}")
            for fname in my:
                others = ', '.join(f"[{j+1}] {mods[j].get('title','?')}"
                                   for j in conflicts[fname] if j != i)
                print(f"       → {fname}   ←→  {others}")
        else:
            print(f"  [{i+1}] {BOLD}{title}{RESET}  ({nf} files)  {GREEN}✓{RESET}{tag}")

    if n_ok and not force:
        print(f"\n  {CYAN}{n_ok} mod(s) already up to date — skipped{RESET}")

    todo = [i for i, s in enumerate(statuses) if force or s[0] != 'up_to_date']
    if not todo:
        print(f"\n  {GREEN}All mods are already installed and up to date.{RESET}\n"); return

    if conflicts:
        print(f"\n  {YELLOW}{len(conflicts)} conflict(s) — last installed wins.{RESET}\n")
    else:
        print(f"\n  {GREEN}No conflicts.{RESET}")

    if yes:
        sel_idx = todo
    else:
        try:
            rep = input(
                f"  Mods to install (e.g.: {' '.join(str(i+1) for i in todo)})"
                f", 'all', empty = cancel: "
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print(); _info("Cancelled."); return
        if not rep:
            _info("Cancelled."); return
        if rep.lower() in ('all', 'y', 'yes'):
            sel_idx = todo
        else:
            try:
                sel_idx = [int(x) - 1 for x in rep.split() if x.isdigit()]
            except (ValueError, IndexError):
                _err(f"Invalid input: {rep!r}"); return

    if not sel_idx:
        _info("No mod selected."); return

    ok = sum(install_mod(mods[i], game_dir, mod_files[i]) for i in sel_idx)
    _ok(f"{ok}/{len(sel_idx)} mod(s) installed")


def cmd_status(game_dir: Path, mods_dir: Path, state: dict) -> None:
    """Displays the status of all mods (browser, ASI, ReShade, patches, overlays)."""
    from . import bin64 as _bin64

    bin64_dir = game_dir / 'bin64'
    overlays  = state.get('overlays', {})
    instd     = _installed_versions(game_dir, mods_dir)

    browser = [m for m in list_mods(mods_dir) if not m.get('_patch_format')]
    print(f"\n  {BOLD}Browser mods{RESET}\n")
    for m in browser:
        mid  = m.get('id', m['_path'].name)
        ver  = str(m.get('version', '?'))
        inst = instd.get(mid)
        tag  = (f"{CYAN}[✓ v{inst}]{RESET}"         if inst == ver else
                f"{YELLOW}[↑ v{inst}→v{ver}]{RESET}" if inst        else
                "[not installed]")
        enbl = f"  {YELLOW}[disabled]{RESET}" if not m.get('enabled', True) else ''
        print(f"    {BOLD}{m.get('title', mid)}{RESET}  v{ver}  {tag}{enbl}")
    if not browser:
        print("    No browser mods.")

    for profile, sub_dir in ((_bin64.ASI, 'asi'), (_bin64.RESHADE, 'reshade')):
        mod_list = _bin64.list_mods(mods_dir / sub_dir, profile)
        label    = profile['label']
        print(f"\n  {BOLD}{label}{RESET}\n")
        for m in mod_list:
            ver  = str(m.get('version', '?'))
            inst = _bin64.installed_version(bin64_dir, m['id'], profile)
            tag  = (f"{CYAN}[✓ v{inst}]{RESET}"         if inst == ver else
                    f"{YELLOW}[↑ v{inst}→v{ver}]{RESET}" if inst        else
                    "[not installed]")
            print(f"    {BOLD}{m['title']}{RESET}  v{ver}  {tag}")
        if not mod_list:
            print(f"    No {label} mods.")

    patches = [m for m in list_mods(mods_dir / 'patch') if m.get('_patch_format')]
    print(f"\n  {BOLD}Patch mods{RESET}\n")
    for m in patches:
        mid  = m.get('id', m['_path'].name)
        ver  = str(m.get('version', '?'))
        inst = instd.get(mid)
        tag  = (f"{CYAN}[✓ v{inst}]{RESET}"           if inst == ver else
                f"{YELLOW}[↑ v{inst}→v{ver}]{RESET}"  if inst        else
                "[not installed]")
        print(f"    {BOLD}{m.get('title', mid)}{RESET}  v{ver}  (fmt {m.get('_patch_format')})"
              f"  {tag}")
    if not patches:
        print("    No patches (mods/patch/ empty or missing).")

    print(f"\n  {BOLD}Installed overlays ({len(overlays)}){RESET}\n")
    for folder, info in sorted(overlays.items()):
        nf  = len(info.get('files', []))
        psz = info.get('paz_size', 0)
        print(f"    {BOLD}{folder}{RESET}  {info.get('content','?')}  ({nf} files, {psz:,} B)")
    if not overlays:
        print("    No overlay installed.")
    print()
