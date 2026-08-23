"""ASI/DLL and ReShade mods: discovery in mods/asi|reshade/ and copy to bin64/."""

import json
import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from .display import _ok, _info, _err, GREEN, YELLOW, CYAN, RESET, BOLD

ASI = {
    'exts':   {'.asi', '.dll', '.ini', '.toml'},
    'prefix': 'asimod',
    'label':  'ASI / DLL',
}
RESHADE = {
    'exts':   {'.addon', '.addon64', '.dll', '.ini'},
    'prefix': 'reshademod',
    'label':  'ReShade',
}


def _version(stem: str) -> str:
    m = re.search(r'[vV]?(\d+\.\d+(?:\.\d+)*)', stem)
    return m.group(1) if m else '?'


def _title(stem: str) -> str:
    t = re.sub(r'-\d+(?:-\d+){2,}$', '', stem)
    t = re.sub(r'\s*[vV]?\d+\.\d+[\d.]*\s*$', '', t)
    return t.strip('-_ ') or stem


def _safe_id(s: str) -> str:
    return re.sub(r'[^\w\-]', '_', s).strip('_')


def _modinfo(path: Path) -> dict:
    for name in ('modinfo.json', 'manifest.json', 'mod.json'):
        p = path / name
        if p.is_file():
            try:
                return json.loads(p.read_text(encoding='utf-8'))
            except Exception:
                pass
    return {}


def list_mods(mods_dir: Path, profile: dict) -> list[dict]:
    """Returns mods from mods_dir (ZIPs or folders) filtered by profile."""
    result = []
    if not mods_dir.is_dir():
        return result
    exts = profile['exts']
    for entry in sorted(mods_dir.iterdir()):
        if entry.suffix.lower() == '.zip':
            try:
                with zipfile.ZipFile(entry) as zf:
                    files = [n for n in zf.namelist()
                             if not n.endswith('/') and Path(n).suffix.lower() in exts]
            except Exception:
                continue
            if not files:
                continue
            t = _title(entry.stem)
            result.append({
                'id': _safe_id(t), 'title': t, 'version': _version(entry.stem),
                '_path': entry, '_zip': True, '_files': files,
            })
        elif entry.is_dir():
            files = [f for f in entry.rglob('*')
                     if f.is_file() and f.suffix.lower() in exts]
            if not files:
                continue
            info = _modinfo(entry)
            t    = info.get('title', entry.name)
            result.append({
                'id': info.get('id', _safe_id(t)), 'title': t,
                'version': str(info.get('version', '?')),
                '_path': entry, '_dir': True, '_files': files,
            })
    return result


def installed_version(bin64: Path, mod_id: str, profile: dict) -> str | None:
    """Installed version in bin64/, or None if absent."""
    p = bin64 / f'.{profile["prefix"]}_{mod_id}'
    if not p.is_file():
        return None
    for line in p.read_text(errors='ignore').splitlines():
        if line.startswith('Version:'):
            return line.split(':', 1)[1].strip()
    return '?'


def install(mod: dict, bin64: Path, profile: dict) -> bool:
    """Copies mod files to bin64/."""
    if not bin64.is_dir():
        _err(f"bin64/ not found: {bin64}"); return False
    name = mod['title']
    _info(f"Installing '{name}' → bin64/ ...")
    try:
        if mod.get('_zip'):
            with zipfile.ZipFile(mod['_path']) as zf:
                for n in mod['_files']:
                    data = zf.read(n)
                    (bin64 / Path(n).name).write_bytes(data)
                    _info(f"  {Path(n).name}  ({len(data):,} B)")
        else:
            for src in mod['_files']:
                shutil.copy2(src, bin64 / src.name)
                _info(f"  {src.name}  ({src.stat().st_size:,} B)")
    except Exception as e:
        _err(f"Error: {e}"); return False
    (bin64 / f'.{profile["prefix"]}_{mod["id"]}').write_text(
        f"{profile['prefix']}  {datetime.now().isoformat(timespec='seconds')}\n"
        f"Mod: {name}  id={mod['id']}\nVersion: {mod['version']}\n"
    )
    _ok(f"'{name}' → bin64/")
    return True


def _version_gt(new_ver: str, old_ver: str) -> bool:
    """True if new_ver > old_ver — numeric segment comparison."""
    def parts(v: str) -> list:
        return [int(x) if x.isdigit() else x for x in re.split(r'[.\-_]', str(v).strip())]
    try:
        return parts(new_ver) > parts(old_ver)
    except TypeError:
        return str(new_ver) != str(old_ver)


def cmd_update(mods_dir: Path, bin64: Path, profile: dict, yes: bool = False) -> int:
    """Installs only mods whose available version > installed version."""
    mods = list_mods(mods_dir, profile)
    updates = []
    for m in mods:
        inst = installed_version(bin64, m['id'], profile)
        if inst and inst != '?' and _version_gt(m['version'], inst):
            updates.append((m, inst, m['version']))

    if not updates:
        return 0

    label = profile['label']
    print(f"\n  {BOLD}{label} updates — {len(updates)} mod(s){RESET}\n")
    for m, old_ver, new_ver in updates:
        print(f"  {YELLOW}↑{RESET}  {BOLD}{m['title']}{RESET}  v{old_ver} → v{new_ver}")
    print()

    if not yes:
        try:
            rep = input("  Update? [y/N]  ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(); _info("Cancelled."); return 0
        if rep not in ('y', 'yes'):
            _info("Cancelled."); return 0

    ok = sum(install(m, bin64, profile) for m, _, _ in updates)
    _ok(f"{ok}/{len(updates)} {label} mod(s) updated")
    return ok


def cmd_dry_run(mods_dir: Path, bin64: Path, profile: dict, force: bool = False, yes: bool = False) -> None:
    """Displays available mods and offers to install them."""
    mods = list_mods(mods_dir, profile)
    if not mods:
        return

    statuses = []
    for m in mods:
        inst = installed_version(bin64, m['id'], profile)
        if inst is None:           statuses.append(('new',))
        elif inst == m['version']: statuses.append(('ok', inst))
        else:                      statuses.append(('up', inst, m['version']))

    label = profile['label']
    n_ok  = sum(1 for s in statuses if s[0] == 'ok')
    print(f"\n  {BOLD}{label} — {len(mods)} mod(s){RESET}\n")
    for i, m in enumerate(mods):
        s   = statuses[i]
        tag = (f"  {CYAN}[✓ v{s[1]}]{RESET}"           if s[0] == 'ok' else
               f"  {YELLOW}[↑ v{s[1]}→v{s[2]}]{RESET}" if s[0] == 'up' else
               f"  {GREEN}[new]{RESET}")
        print(f"  [a{i+1}] {BOLD}{m['title']}{RESET}  ({len(m['_files'])} file(s)){tag}")

    if n_ok and not force:
        print(f"\n  {CYAN}{n_ok} already up to date — skipped{RESET}")

    todo = [i for i, s in enumerate(statuses) if force or s[0] != 'ok']
    if not todo:
        print(f"\n  {GREEN}Everything is up to date.{RESET}\n"); return

    if yes:
        sel_idx = todo
    else:
        print()
        try:
            rep = input(
                f"  {label} to install (e.g.: {' '.join(f'a{i+1}' for i in todo)})"
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
                sel_idx = [int(x.lstrip('a')) - 1 for x in rep.split() if x.lstrip('a').isdigit()]
            except (ValueError, IndexError):
                _err(f"Invalid input: {rep!r}"); return

    ok = sum(install(mods[i], bin64, profile) for i in sel_idx)
    _ok(f"{ok}/{len(sel_idx)} {label} mod(s) installed")
