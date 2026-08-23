"""Mod discovery and reading (extracted folders, ZIPs and 7zip archives)."""

import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from .display import _warn

_SKIP_FILES = {'manifest.json', 'modinfo.json', 'mod.json'}

# ── Helpers 7zip ──────────────────────────────────────────────────────────────

_7Z_CMD: str | None = None
_7Z_CHECKED = False


def _get_7z_cmd() -> str | None:
    """Finds the available 7z binary (result cached)."""
    global _7Z_CMD, _7Z_CHECKED
    if _7Z_CHECKED:
        return _7Z_CMD
    _7Z_CHECKED = True
    candidates = [
        '7z', '7za', '7zz',
        '/usr/lib/p7zip/7z',
        '/usr/lib/p7zip/7za',
        '/usr/lib/7zip/7z',
        '/usr/lib/7zip/7zz',
    ]
    for cmd in candidates:
        if shutil.which(cmd) or not cmd.startswith('/'):
            try:
                subprocess.run([cmd], capture_output=True, timeout=5)
                _7Z_CMD = cmd
                return cmd
            except FileNotFoundError:
                continue
        elif Path(cmd).is_file():
            _7Z_CMD = cmd
            return cmd
    return None


def _7z_list(archive_path: Path) -> list[str]:
    """Lists files (not folders) in an archive via 7z."""
    cmd = _get_7z_cmd()
    if not cmd:
        return []
    try:
        r = subprocess.run(
            [cmd, 'l', '-slt', str(archive_path)],
            capture_output=True, timeout=60,
        )
        output = r.stdout.decode('utf-8', errors='replace')

        # Each "Path = " marks a new entry; "----------" resets.
        # Multiple entries may appear in the same block (without ---------- between them).
        files: list[str] = []
        cur_path   = ''
        cur_folder = '-'
        in_entries = False

        for line in output.splitlines():
            stripped = line.strip()
            if stripped and all(c == '-' for c in stripped) and len(stripped) >= 10:
                # Save current entry if it is a file
                if in_entries and cur_path and cur_folder != '+':
                    files.append(cur_path)
                in_entries = True
                cur_path   = ''
                cur_folder = '-'
            elif in_entries:
                if line.startswith('Path = '):
                    # New entry in same block → save the previous one
                    if cur_path and cur_folder != '+':
                        files.append(cur_path)
                    cur_path   = line[7:]
                    cur_folder = '-'
                elif line.startswith('Folder = '):
                    cur_folder = line[9:].strip()

        # Last entry
        if in_entries and cur_path and cur_folder != '+':
            files.append(cur_path)

        return files
    except Exception as e:
        _warn(f"Error reading archive {archive_path.name}: {e}")
        return []


def _7z_read(archive_path: Path, internal_path: str) -> bytes | None:
    """Extracts a file from an archive via 7z, returns its bytes."""
    cmd = _get_7z_cmd()
    if not cmd:
        return None
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            r = subprocess.run(
                [cmd, 'e', '-y', f'-o{tmpdir}', str(archive_path), internal_path],
                capture_output=True, timeout=60,
            )
            if r.returncode != 0:
                return None
            filename = internal_path.replace('\\', '/').split('/')[-1]
            outfile  = Path(tmpdir) / filename
            if outfile.is_file():
                return outfile.read_bytes()
        except Exception:
            pass
    return None


# ── Lecture des manifests ─────────────────────────────────────────────────────

def _zip_peek_manifest(zip_path: Path) -> dict | None:
    """Reads manifest.json from inside a ZIP without extracting it."""
    try:
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            for name in sorted(names, key=lambda n: n.count('/')):
                if name.split('/')[-1] == 'manifest.json' and name.count('/') <= 10:
                    return json.loads(zf.read(name).decode('utf-8'))
    except Exception as e:
        _warn(f"Cannot read {zip_path.name}: {e}")
    return None


def _archive_peek_manifest(archive_path: Path) -> dict | None:
    """Reads or generates a manifest from a 7zip archive (RAR, 7z, …)."""
    if not _get_7z_cmd():
        _warn(f"{archive_path.name}: 7zip not found — install 7zip")
        return None
    try:
        names    = _7z_list(archive_path)
        norm_map = {n.replace('\\', '/'): n for n in names}

        # Look for an existing manifest.json
        candidates = sorted(
            [(norm, orig) for norm, orig in norm_map.items()
             if norm.split('/')[-1] == 'manifest.json' and norm.count('/') <= 10],
            key=lambda x: x[0].count('/'),
        )
        for norm, orig in candidates:
            data = _7z_read(archive_path, orig)
            if data is not None:
                return json.loads(data.decode('utf-8'))

        # No manifest.json — generate a minimal manifest from the structure
        if not norm_map:
            return None
        root = sorted({n.split('/')[0] for n in norm_map if n})[0]
        return {
            'id':      re.sub(r'[^\w\-.]', '_', root),
            'title':   root,
            'version': '?',
            'author':  '?',
        }
    except Exception as e:
        _warn(f"Cannot read {archive_path.name}: {e}")
    return None


# ── Découverte des mods ───────────────────────────────────────────────────────

_ARCHIVE_EXTS = {'.rar', '.7z'}


def list_mods(mods_dir: Path) -> list[dict]:
    """Returns all mods in mods_dir (extracted folders, ZIPs and archives)."""
    result = []
    if not mods_dir.is_dir():
        return result

    for entry in sorted(mods_dir.iterdir()):
        if entry.is_dir():
            mp = entry / 'manifest.json'
            if not mp.is_file():
                continue
            try:
                m = json.loads(mp.read_text(encoding='utf-8'))
                m['_path'] = entry
                result.append(m)
            except Exception as e:
                _warn(f"Invalid manifest.json in {entry.name}: {e}")

        elif entry.suffix.lower() == '.zip':
            m = _zip_peek_manifest(entry)
            if not m:
                continue
            mod_id  = m.get('id') or entry.stem
            safe_id = re.sub(r'[^\w\-.]', '_', mod_id)
            m['_path']     = mods_dir / safe_id
            m['_is_zip']   = True
            m['_zip_path'] = entry
            result.append(m)

        elif entry.suffix.lower() in _ARCHIVE_EXTS:
            m = _archive_peek_manifest(entry)
            if not m:
                continue
            mod_id  = m.get('id') or entry.stem
            safe_id = re.sub(r'[^\w\-.]', '_', mod_id)
            m['_path']         = mods_dir / safe_id
            m['_is_archive']   = True
            m['_archive_path'] = entry
            result.append(m)

        elif entry.suffix.lower() == '.json':
            try:
                data    = json.loads(entry.read_text(encoding='utf-8-sig'))
                fmt     = int(data.get('format', 0))
                patches = data.get('patches', [])
                if fmt == 0 and patches and isinstance(patches[0], dict) and 'changes' in patches[0]:
                    fmt = 2
                if fmt not in (2, 3):
                    continue
                modinfo = data.get('modinfo', {})
                result.append({
                    'id':            entry.stem,
                    'title':         modinfo.get('title') or data.get('name', entry.stem),
                    'author':        modinfo.get('author') or data.get('author', '?'),
                    'version':       modinfo.get('version') or data.get('version', '?'),
                    '_path':         entry,
                    '_patch_format': fmt,
                })
            except Exception as e:
                _warn(f"Invalid JSON patch {entry.name}: {e}")

    return result


# ── Collecte des fichiers de mod ──────────────────────────────────────────────

def _collect_zip_files(mod: dict) -> list[tuple[str, str, object]]:
    """Lists files in a ZIP mod without extracting it."""
    zip_path   = mod.get('_zip_path')
    configured = mod.get('files_dir', 'files')
    result: list[tuple[str, str, object]] = []

    try:
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            manifest_name = next(
                (n for n in sorted(names, key=lambda x: x.count('/'))
                 if n.split('/')[-1] == 'manifest.json' and n.count('/') <= 10),
                None,
            )
            if not manifest_name:
                return []

            mod_root     = '/'.join(manifest_name.split('/')[:-1])
            base_prefix  = (mod_root + '/') if mod_root else ''
            files_prefix = base_prefix + configured + '/'
            fp_low       = files_prefix.lower()
            matching     = [n for n in names if n.lower().startswith(fp_low)]

            if not matching:
                files_prefix = base_prefix
                fp_low       = files_prefix.lower()
                matching     = [n for n in names if n.lower().startswith(fp_low)]

            for name in matching:
                rel = name[len(files_prefix):]
                if not rel or rel.endswith('/'):
                    continue
                parts = tuple(rel.split('/'))
                if parts[-1].lower() in _SKIP_FILES:
                    continue
                inner    = parts[1:] if len(parts) >= 2 and parts[0].isdigit() else parts
                dir_path = '/'.join(inner[:-1]) if len(inner) > 1 else ''
                result.append((dir_path, inner[-1], (zip_path, name)))
    except Exception as e:
        _warn(f"Error reading ZIP {zip_path}: {e}")

    return result


def _collect_archive_files(mod: dict) -> list[tuple[str, str, object]]:
    """Lists files in a 7zip archive mod (RAR, 7z, …) without extracting it."""
    if not _get_7z_cmd():
        _warn("7zip not found — install 7zip")
        return []
    archive_path = mod.get('_archive_path')
    configured   = mod.get('files_dir', 'files')
    result: list[tuple[str, str, object]] = []

    try:
        raw_names  = _7z_list(archive_path)
        norm_map   = {n.replace('\\', '/'): n for n in raw_names}
        norm_names = list(norm_map)

        manifest_norm = next(
            (n for n in sorted(norm_names, key=lambda x: x.count('/'))
             if n.split('/')[-1] == 'manifest.json' and n.count('/') <= 10),
            None,
        )
        if manifest_norm:
            mod_root = '/'.join(manifest_norm.split('/')[:-1])
        else:
            # No manifest.json — derive root folder from paths
            roots = {n.split('/')[0] for n in norm_names if n}
            mod_root = sorted(roots)[0] if roots else ''
        base_prefix  = (mod_root + '/') if mod_root else ''
        files_prefix = base_prefix + configured + '/'
        fp_low       = files_prefix.lower()
        matching     = [n for n in norm_names if n.lower().startswith(fp_low)]

        if not matching:
            files_prefix = base_prefix
            fp_low       = files_prefix.lower()
            matching     = [n for n in norm_names if n.lower().startswith(fp_low)]

        for norm in matching:
            rel = norm[len(files_prefix):]
            if not rel or rel.endswith('/'):
                continue
            parts = tuple(rel.split('/'))
            if parts[-1].lower() in _SKIP_FILES:
                continue
            inner    = parts[1:] if len(parts) >= 2 and parts[0].isdigit() else parts
            dir_path = '/'.join(inner[:-1]) if len(inner) > 1 else ''
            result.append((dir_path, inner[-1], (archive_path, norm_map[norm])))
    except Exception as e:
        _warn(f"Error reading archive {archive_path}: {e}")

    return result


def collect_mod_files(mod: dict) -> list[tuple[str, str, object]]:
    """
    Returns [(dir_path_PAZ, filename, source)] for a mod.
    Works for extracted mods, ZIPs and 7zip archives without extraction.
    """
    if mod.get('_is_zip') and not mod['_path'].is_dir():
        return _collect_zip_files(mod)
    if mod.get('_is_archive') and not mod['_path'].is_dir():
        return _collect_archive_files(mod)
    if not mod['_path'].is_dir():
        return []

    base       = Path(mod['_path'])
    configured = mod.get('files_dir', 'files')
    files_dir  = base / configured

    if not files_dir.is_dir():
        lower     = configured.lower()
        files_dir = next(
            (base / d for d in os.listdir(base)
             if d.lower() == lower and (base / d).is_dir()),
            base,
        )

    # Only strip a leading numeric folder if it's a single wrapper folder,
    # not when the mod ships multiple distinct numbered overlay dirs.
    top_numeric = {
        f.relative_to(files_dir).parts[0]
        for f in files_dir.rglob('*')
        if f.is_file() and f.name.lower() not in _SKIP_FILES
        and f.relative_to(files_dir).parts[0].isdigit()
    }
    strip_wrapper = len(top_numeric) <= 1

    result: list[tuple[str, str, object]] = []
    for f in files_dir.rglob('*'):
        if not f.is_file() or f.name.lower() in _SKIP_FILES:
            continue
        parts    = f.relative_to(files_dir).parts
        inner    = parts[1:] if (strip_wrapper and len(parts) >= 2 and parts[0].isdigit()) else parts
        dir_path = '/'.join(inner[:-1]) if len(inner) > 1 else ''
        result.append((dir_path, inner[-1], f))

    return result
