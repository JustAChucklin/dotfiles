"""Management of Crimson Desert's meta/0.papgt file.

Actual format verified on vanilla file:
  [0:4]   magic
  [4:8]   file_hash = hashlittle(papgt[12:], 0xC5EDE)
  [8:12]  meta8 — byte[8] = entry_count, bytes[9-11] = 0x000200
  [12:]   N × 12-byte entries
            [flags(4), name_offset(4), pamt_hash(4)]
  [12+N*12:] string_table_size (4 bytes LE)
  [12+N*12+4:] string table (null-terminated ASCII dir names)
"""

import json
import os
import re
import shutil
import struct
import sys
from datetime import datetime
from pathlib import Path

from .config  import CACHE_FILE, BACKUP_KEEP
from .crypto  import hashlittle, HASH_SEED
from .display import _ok, _info, _warn, _err, BOLD, RESET, GREEN, YELLOW, RED

FLAGS_MOD   = 0x003FFF00   # is_optional=0, lang_type=0x3FFF, zero=0
VANILLA_MAX = 99
ENTRY_SIZE  = 12
HEADER_SIZE = 12


# ── Hash d'un 0.pamt ──────────────────────────────────────────────────────────

def hash_pamt(path: Path) -> int:
    data = path.read_bytes()
    if len(data) < 12:
        raise ValueError(f"0.pamt trop court : {path}")
    return hashlittle(data[12:], HASH_SEED)


# ── Parse / construction du 0.papgt ──────────────────────────────────────────

def _find_entry_count(data: bytes) -> int:
    """Determines the number of entries by locating the string table size field."""
    file_size = len(data)
    for n in range(1, 200):
        size_field_pos = HEADER_SIZE + n * ENTRY_SIZE
        if size_field_pos + 4 > file_size:
            break
        st_size = struct.unpack_from('<I', data, size_field_pos)[0]
        if size_field_pos + 4 + st_size == file_size:
            return n
    raise ValueError("Cannot locate entry count in 0.papgt")


def parse_papgt(data: bytes) -> dict:
    if len(data) < HEADER_SIZE:
        raise ValueError(f"File too short ({len(data)} bytes)")

    magic,     = struct.unpack_from('<I', data, 0)
    file_hash, = struct.unpack_from('<I', data, 4)
    meta8,     = struct.unpack_from('<I', data, 8)

    n_entries   = _find_entry_count(data)
    st_size_pos = HEADER_SIZE + n_entries * ENTRY_SIZE
    st_size,    = struct.unpack_from('<I', data, st_size_pos)
    st_start    = st_size_pos + 4
    st_data     = data[st_start:]

    names: dict[int, str] = {}
    pos = 0
    while pos < len(st_data):
        end = st_data.find(b'\x00', pos)
        if end == -1:
            break
        names[pos] = st_data[pos:end].decode('utf-8', errors='replace')
        pos = end + 1

    entries = []
    for i in range(n_entries):
        off = HEADER_SIZE + i * ENTRY_SIZE
        flags, name_off, pamt_hash = struct.unpack_from('<III', data, off)
        entries.append({
            'name':      names.get(name_off, f'?off={name_off}'),
            'pamt_hash': pamt_hash,
            'flags':     flags,
        })

    return {'magic': magic, 'file_hash': file_hash, 'meta8': meta8, 'entries': entries}


def build_papgt(parsed: dict) -> bytes:
    entries = parsed['entries']

    name_offsets: dict[str, int] = {}
    st_bytes = b''
    for e in entries:
        if e['name'] not in name_offsets:
            name_offsets[e['name']] = len(st_bytes)
            st_bytes += e['name'].encode('utf-8') + b'\x00'

    entry_bytes = b''.join(
        struct.pack('<III', e['flags'], name_offsets[e['name']], e['pamt_hash'])
        for e in entries
    )

    # byte[8] = entry_count, bytes[9-11] preserved from meta8
    meta8         = parsed.get('meta8', 0)
    meta8_updated = (meta8 & 0xFFFFFF00) | (len(entries) & 0xFF)

    body = (
        struct.pack('<I', parsed['magic'])
        + b'\x00\x00\x00\x00'              # file_hash placeholder
        + struct.pack('<I', meta8_updated)
        + entry_bytes
        + struct.pack('<I', len(st_bytes)) # string table size
        + st_bytes
    )

    h = hashlittle(body[12:], HASH_SEED)
    return body[:4] + struct.pack('<I', h) + body[8:]


# ── Cache vanilla ─────────────────────────────────────────────────────────────

def load_cache(meta_dir: Path) -> dict | None:
    path = meta_dir / CACHE_FILE
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e:
        _warn(f"Unreadable cache ({e}) — will be recreated")
        return None


def save_cache(meta_dir: Path, cache: dict) -> None:
    path = meta_dir / CACHE_FILE
    tmp  = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(cache, indent=2), encoding='utf-8')
    tmp.replace(path)


def _get_meta8(cache: dict) -> int:
    """Retrieves meta8 from cache (backward compatibility with old unk1 format)."""
    hdr = cache.get('header', {})
    if 'meta8' in hdr:
        return hdr['meta8']
    # Old format: unk1 = 0x200 + entry_count — preserve the 0x200 base
    return hdr.get('unk1', 0) & 0xFFFFFF00


def _vanilla_ref_hash(cache: dict) -> int:
    entries = [
        {'name': n, 'pamt_hash': d['pamt_hash'], 'flags': d['flags']}
        for n, d in sorted(cache['vanilla'].items(), key=lambda x: int(x[0]))
    ]
    ref = build_papgt({
        'magic':     cache['header']['magic'],
        'file_hash': 0,
        'meta8':     _get_meta8(cache),
        'entries':   entries,
    })
    return struct.unpack_from('<I', ref, 4)[0]


def create_cache(game_dir: Path, parsed: dict) -> dict:
    vanilla: dict[str, dict] = {}
    for e in parsed['entries']:
        name = e['name']
        if not re.match(r'^\d{4}$', name) or int(name) > VANILLA_MAX:
            continue
        pamt = game_dir / name / '0.pamt'
        if not pamt.is_file():
            vanilla[name] = {'pamt_hash': e['pamt_hash'], 'flags': e['flags']}
            continue
        h = hash_pamt(pamt)
        if h != e['pamt_hash']:
            _warn(f"{name}: computed hash ({h:#010x}) ≠ papgt ({e['pamt_hash']:#010x}) — keeping computed")
        vanilla[name] = {'pamt_hash': h, 'flags': e['flags']}

    cache: dict = {
        'version':    2,
        'created_at': datetime.now().isoformat(timespec='seconds'),
        'updated_at': datetime.now().isoformat(timespec='seconds'),
        'header': {
            'magic': parsed['magic'],
            'meta8': parsed['meta8'],
        },
        'vanilla': vanilla,
    }
    cache['papgt_hash'] = _vanilla_ref_hash(cache)
    return cache


def refresh_cache(game_dir: Path, cache: dict) -> dict:
    meta_dir = game_dir / 'meta'
    origin_vanilla = _origin_vanilla(_find_latest_origin(meta_dir) or {'entries': []})

    new_vanilla: dict[str, dict] = {}
    for name, entry in cache['vanilla'].items():
        if name in origin_vanilla:
            new_h = origin_vanilla[name]['pamt_hash']
            if new_h != entry['pamt_hash']:
                _ok(f"  {name}  {entry['pamt_hash']:#010x} → {new_h:#010x}  [origin]")
            new_vanilla[name] = {'pamt_hash': new_h, 'flags': origin_vanilla[name]['flags']}
        else:
            pamt = game_dir / name / '0.pamt'
            if pamt.is_file():
                h = hash_pamt(pamt)
                if h != entry['pamt_hash']:
                    _ok(f"  {name}  {entry['pamt_hash']:#010x} → {h:#010x}")
                new_vanilla[name] = {'pamt_hash': h, 'flags': entry['flags']}
            else:
                new_vanilla[name] = entry

    cache['vanilla']    = new_vanilla
    cache['updated_at'] = datetime.now().isoformat(timespec='seconds')
    cache['papgt_hash'] = _vanilla_ref_hash(cache)
    return cache


def _find_latest_origin(meta_dir: Path) -> dict | None:
    origins = sorted(meta_dir.glob('0.papgt.origin.*'), key=lambda p: p.stat().st_mtime)
    for origin in reversed(origins):
        try:
            return parse_papgt(origin.read_bytes())
        except Exception:
            continue
    return None


def _origin_vanilla(origin: dict) -> dict[str, dict]:
    return {
        e['name']: {'pamt_hash': e['pamt_hash'], 'flags': e['flags']}
        for e in origin['entries']
        if re.match(r'^\d{4}$', e['name']) and int(e['name']) <= VANILLA_MAX
    }


def game_updated(game_dir: Path, cache: dict) -> bool:
    meta_dir = game_dir / 'meta'

    for name, entry in cache['vanilla'].items():
        pamt = game_dir / name / '0.pamt'
        if not pamt.is_file():
            continue
        try:
            if hash_pamt(pamt) != entry['pamt_hash']:
                return True
        except Exception:
            continue

    origin = _find_latest_origin(meta_dir)
    if origin is None:
        return False
    for name, data in _origin_vanilla(origin).items():
        if name in cache['vanilla'] and data['pamt_hash'] != cache['vanilla'][name]['pamt_hash']:
            return True
    return False


# ── Scan des mods ─────────────────────────────────────────────────────────────

def scan_mods(game_dir: Path) -> list[tuple[str, Path]]:
    pattern = re.compile(r'^\d{4}$')
    mods = []
    for name in os.listdir(game_dir):
        if not pattern.match(name):
            continue
        if int(name) > VANILLA_MAX and (game_dir / name / '0.pamt').is_file():
            mods.append((name, game_dir / name / '0.pamt'))
    return sorted(mods, key=lambda x: int(x[0]))


# ── Backup / Restore ──────────────────────────────────────────────────────────

def do_backup(papgt_path: Path) -> None:
    ts   = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = papgt_path.with_name(f'0.papgt.backup_{ts}')
    shutil.copy2(papgt_path, dest)
    _ok(f"Backup created: {dest.name}")

    backups = sorted(papgt_path.parent.glob('0.papgt.backup_*'), reverse=True)
    for old in backups[BACKUP_KEEP:]:
        old.unlink()
        _info(f"Old backup removed: {old.name}")


def do_restore(papgt_path: Path) -> None:
    backups = sorted(papgt_path.parent.glob('0.papgt.backup_*'), reverse=True)
    if not backups:
        _err("No backup found in meta/")
        sys.exit(1)

    print(f"\n  {BOLD}Available backups:{RESET}\n")
    for i, b in enumerate(backups):
        print(f"  [{i+1}] {b.name}  ({b.stat().st_size} bytes)")
    print(f"  [0] Cancel\n")

    try:
        rep = input("  Backup number to restore: ").strip()
    except (EOFError, KeyboardInterrupt):
        print(); _info("Cancelled."); return

    if rep in ('0', ''):
        _info("Cancelled."); return

    try:
        chosen = backups[int(rep) - 1]
    except (ValueError, IndexError):
        _err(f"Invalid choice: {rep!r}"); sys.exit(1)

    do_backup(papgt_path)
    shutil.copy2(chosen, papgt_path)
    _ok(f"Restored from: {chosen.name}")
    _ok("meta/0.papgt successfully replaced")


# ── Entry point ───────────────────────────────────────────────────────────────

def run(game_dir: Path, recache: bool = False, restore: bool = False, yes: bool = False) -> None:
    meta_dir   = game_dir / 'meta'
    papgt_path = meta_dir / '0.papgt'

    if not meta_dir.is_dir():
        _err(f"meta/ directory not found: {meta_dir}"); sys.exit(1)

    if restore:
        do_restore(papgt_path); return

    cache = load_cache(meta_dir)

    if cache is None or recache:
        if not papgt_path.is_file():
            _err(
                "No cache and 0.papgt not found.\n"
                "Place a vanilla 0.papgt in meta/ for the first run."
            ); sys.exit(1)
        parsed_boot = parse_papgt(papgt_path.read_bytes())
        if cache is None:
            _info("First run — creating vanilla cache...")
            cache = create_cache(game_dir, parsed_boot)
            save_cache(meta_dir, cache)
            _ok(f"Cache created ({len(cache['vanilla'])} vanilla entries)")
        else:
            _info("Forcing vanilla hash recomputation...")
            cache = refresh_cache(game_dir, cache)
            save_cache(meta_dir, cache)
            _ok("Vanilla cache updated")
        print()
    elif game_updated(game_dir, cache):
        _warn("Game update detected — recomputing vanilla hashes...")
        cache = refresh_cache(game_dir, cache)
        save_cache(meta_dir, cache)
        _ok("Vanilla cache updated")
        print()

    old_entries: list[dict] = []
    old_meta8:   int        = 0
    if papgt_path.is_file():
        try:
            parsed_old  = parse_papgt(papgt_path.read_bytes())
            old_entries = parsed_old['entries']
            old_meta8   = parsed_old['meta8']
        except Exception:
            pass

    mods = scan_mods(game_dir)
    mod_by_name = {
        name: {'name': name, 'pamt_hash': hash_pamt(pamt), 'flags': FLAGS_MOD}
        for name, pamt in mods
    }
    vanilla_by_name = {
        n: {'name': n, 'pamt_hash': d['pamt_hash'], 'flags': d['flags']}
        for n, d in cache['vanilla'].items()
    }

    seen: set[str] = set()
    target_entries: list[dict] = []

    # 1. Mods FIRST, descending order
    for name in sorted(mod_by_name, key=lambda x: int(x), reverse=True):
        target_entries.append(mod_by_name[name])
        seen.add(name)

    # 2. Existing non-vanilla non-mod entries → preserved only if 0.pamt still exists
    for e in old_entries:
        name = e['name']
        if name in seen or name in vanilla_by_name:
            continue
        if not (game_dir / name / '0.pamt').is_file():
            continue
        target_entries.append(e)
        seen.add(name)

    # 3. Vanilla LAST, ascending order
    for n in sorted(vanilla_by_name, key=lambda x: int(x)):
        target_entries.append(vanilla_by_name[n])
        seen.add(n)

    new_map = {e['name']: e['pamt_hash'] for e in target_entries}
    old_map  = {e['name']: e['pamt_hash'] for e in old_entries}

    additions = [(n, h)          for n, h in new_map.items() if n not in old_map]
    deletions = [(n, old_map[n]) for n in old_map            if n not in new_map]
    changes   = [(n, old_map[n], new_map[n])
                 for n in new_map if n in old_map and old_map[n] != new_map[n]]

    if not additions and not deletions and not changes:
        _ok("meta/0.papgt is already up to date."); return

    n_foreign = len([e for e in target_entries
                     if e['name'] not in vanilla_by_name and e['name'] not in mod_by_name])
    print(f"\n  {BOLD}Detected changes:{RESET}\n")
    for name, h in sorted(additions, key=lambda x: x[0]):
        print(f"  {GREEN}+{RESET} {name}   new                  hash: {h:#010x}")
    for name, old_h, new_h in sorted(changes, key=lambda x: x[0]):
        print(f"  {YELLOW}~{RESET} {name}   hash changed          {old_h:#010x} → {new_h:#010x}")
    for name, h in sorted(deletions, key=lambda x: x[0]):
        print(f"  {RED}-{RESET} {name}   removed               hash: {h:#010x}")

    total = len(additions) + len(deletions) + len(changes)
    print(f"\n  {total} change(s)  "
          f"({len(mod_by_name)} mod(s) + {len(vanilla_by_name)} vanilla"
          f"{f' + {n_foreign} foreign' if n_foreign else ''})\n")

    if not yes:
        try:
            rep = input("  Update meta/0.papgt? [y/N]  ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(); _info("Cancelled."); return
        if rep not in ('y', 'yes'):
            _info("Cancelled."); return

    if papgt_path.is_file():
        do_backup(papgt_path)

    meta8 = old_meta8 or _get_meta8(cache)
    out   = build_papgt({
        'magic':     cache['header']['magic'],
        'file_hash': 0,
        'meta8':     meta8,
        'entries':   target_entries,
    })
    new_hash = struct.unpack_from('<I', out, 4)[0]

    tmp = papgt_path.with_suffix('.tmp')
    tmp.write_bytes(out)
    tmp.replace(papgt_path)

    print()
    _ok(f"meta/0.papgt updated")
    _ok(f"Global hash  : {new_hash:#010x}")
    _ok(f"Entries      : {len(target_entries)}  ({len(mod_by_name)} mod(s)"
        f" + {len(vanilla_by_name)} vanilla"
        f"{f' + {n_foreign} foreign' if n_foreign else ''})")
