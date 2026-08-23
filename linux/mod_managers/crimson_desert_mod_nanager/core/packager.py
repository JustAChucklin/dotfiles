"""PAZ format — compression, extraction and archive construction."""

import functools
import importlib.util
import shutil
import struct
import sys
import types
import zipfile
from pathlib import Path

from .config  import CDUMM_SRC, DMM_PARSER_SRC
from .crypto  import hashlittle, chacha20_encrypt, needs_encryption, HASH_SEED
from .display import _warn

_dmm          = None
_cdumm_parser = None


def _get_dmm():
    """Loads dmm_parser once; returns None if unavailable."""
    global _dmm
    if _dmm is not None:
        return _dmm or None  # False = unavailable → None
    src = str(DMM_PARSER_SRC)
    if src not in sys.path:
        sys.path.insert(0, src)
    try:
        import dmm_parser as _m
        _dmm = _m
    except ImportError:
        _dmm = False  # mark as "not found" to avoid retrying
    return _dmm or None


def _get_cdumm_iteminfo_parser():
    """Loads the CDUMM Python parser for iteminfo (independent of the dmm_parser binary).

    Takes priority for Format 3 iteminfo patches because the Python parser
    is updated for every game build (e.g. new field in 1.11),
    without waiting for a binary recompilation.
    """
    global _cdumm_parser
    if _cdumm_parser is not None:
        return _cdumm_parser or None
    if CDUMM_SRC is None:
        _cdumm_parser = False
        return None
    parser_file = Path(CDUMM_SRC) / 'cdumm' / 'engine' / 'iteminfo_native_parser.py'
    if not parser_file.is_file():
        _warn(f"CDUMM parser not found: {parser_file}")
        _cdumm_parser = False
        return None
    try:
        spec = importlib.util.spec_from_file_location('_cdumm_iteminfo_parser', parser_file)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _cdumm_parser = types.SimpleNamespace(
            parse_iteminfo_from_bytes=mod.parse_iteminfo_from_bytes,
            serialize_iteminfo=mod.serialize_iteminfo,
        )
    except Exception as e:
        _warn(f"CDUMM parser failed to load: {e}")
        _cdumm_parser = False
    return _cdumm_parser or None

try:
    import lz4.block as _lz4
    _HAS_LZ4 = True
except ImportError:
    _HAS_LZ4 = False

COMP_NONE     = 0
COMP_DDS      = 1
COMP_LZ4      = 2
PAMT_CONSTANT = 0x610E0232
PAZ_ALIGNMENT = 16
VANILLA_MAX   = 35


# ── Compression / préparation payload ────────────────────────────────────────

def _lz4_compress(data: bytes) -> bytes:
    if not _HAS_LZ4:
        raise RuntimeError("Package 'lz4' required: pip install lz4")
    return _lz4.compress(data, store_size=False)


def _infer_comp_type(filename: str) -> int:
    ext = Path(filename).suffix.lower()
    if ext == '.dds': return COMP_DDS
    if ext == '.bnk': return COMP_NONE
    return COMP_LZ4


def prepare_file(src) -> tuple[bytes, int, int, int]:
    """
    Reads a source file and returns (payload, comp_size, orig_size, comp_type).
    src: disk Path, or (zip_path, internal_name) for an unextracted ZIP.
    """
    if isinstance(src, tuple):
        archive_path, internal_name = src
        if Path(archive_path).suffix.lower() in ('.rar', '.7z'):
            from .sources import _7z_read
            data = _7z_read(Path(archive_path), internal_name)
            if data is None:
                raise RuntimeError(f"7zip: cannot extract {internal_name} from {archive_path}")
            plaintext = data
        else:
            with zipfile.ZipFile(archive_path) as zf:
                plaintext = zf.read(internal_name)
        filename = internal_name.replace('\\', '/').split('/')[-1]
    else:
        plaintext = src.read_bytes()
        filename  = src.name

    orig_size = len(plaintext)
    ctype     = _infer_comp_type(filename)

    if ctype in (COMP_NONE, COMP_DDS):
        return plaintext, orig_size, orig_size, ctype

    compressed = _lz4_compress(plaintext)
    payload    = chacha20_encrypt(compressed, filename) if needs_encryption(filename) else compressed
    return payload, len(payload), orig_size, COMP_LZ4


# ── Construction PAZ ──────────────────────────────────────────────────────────

def build_paz(payloads: list[bytes]) -> tuple[bytes, list[int]]:
    """Builds the raw PAZ. Returns (paz_bytes, per_payload_offsets)."""
    paz     = bytearray()
    offsets = []
    for payload in payloads:
        offsets.append(len(paz))
        paz += payload
        paz += b'\x00' * ((-len(paz)) % PAZ_ALIGNMENT)
    return bytes(paz), offsets


# ── Construction PAMT ─────────────────────────────────────────────────────────

def _u32(val: int) -> bytes:
    return struct.pack('<I', val & 0xFFFFFFFF)


def build_pamt(entries: list[dict], paz_data_len: int) -> bytes:
    """
    Builds the 0.pamt for an overlay.
    Each entry: {dir_path, filename, paz_offset, comp_size, orig_size, flags}
    """
    unique_dirs = sorted(set(e['dir_path'] for e in entries))

    folder_bytes:   bytearray      = bytearray()
    folder_offsets: dict[str, int] = {}
    for dir_path in unique_dirs:
        parts = dir_path.split('/') if dir_path else ['']
        for depth in range(len(parts)):
            key = '/'.join(parts[:depth + 1])
            if key in folder_offsets:
                continue
            folder_offsets[key] = len(folder_bytes)
            parent = 0xFFFFFFFF if depth == 0 else folder_offsets['/'.join(parts[:depth])]
            name   = parts[0] if depth == 0 else '/' + parts[depth]
            name_b = name.encode()
            folder_bytes += _u32(parent) + bytes([len(name_b)]) + name_b

    dir_entries: dict[str, list[tuple[int, dict]]] = {}
    for i, e in enumerate(entries):
        dir_entries.setdefault(e['dir_path'], []).append((i, e))
    for group in dir_entries.values():
        group.sort(key=lambda x: x[1]['filename'])

    node_bytes:   bytearray      = bytearray()
    node_offsets: dict[int, int] = {}
    for dir_path in unique_dirs:
        for idx, e in dir_entries.get(dir_path, []):
            node_offsets[idx] = len(node_bytes)
            name_b = e['filename'].encode()
            node_bytes += _u32(0xFFFFFFFF) + bytes([len(name_b)]) + name_b

    folder_records = bytearray()
    file_index     = 0
    for dir_path in unique_dirs:
        group = dir_entries.get(dir_path, [])
        folder_records += (
            _u32(hashlittle(dir_path.encode(), HASH_SEED))
            + _u32(folder_offsets.get(dir_path, 0))
            + _u32(file_index)
            + _u32(len(group))
        )
        file_index += len(group)

    file_records = bytearray()
    for dir_path in unique_dirs:
        for idx, e in dir_entries.get(dir_path, []):
            file_records += (
                _u32(node_offsets[idx])
                + _u32(e['paz_offset'])
                + _u32(e['comp_size'])
                + _u32(e['orig_size'])
                + _u32(e['flags'] << 16)
            )

    body = (
        _u32(1) + _u32(PAMT_CONSTANT) + _u32(0) + _u32(0) + _u32(paz_data_len)
        + _u32(len(folder_bytes)) + bytes(folder_bytes)
        + _u32(len(node_bytes))   + bytes(node_bytes)
        + _u32(len(unique_dirs))  + bytes(folder_records)
        + _u32(file_index)        + bytes(file_records)
    )
    return b'\x00\x00\x00\x00' + body


def finalize_pamt(pamt: bytes, paz_bytes: bytes) -> bytes:
    """Injects the PAZ hash and global hash into the PAMT."""
    pamt = bytearray(pamt)
    struct.pack_into('<I', pamt, 16, hashlittle(paz_bytes, HASH_SEED))
    struct.pack_into('<I', pamt,  0, hashlittle(bytes(pamt[12:]), HASH_SEED))
    return bytes(pamt)


# ── Extraction PAZ ────────────────────────────────────────────────────────────

def _parse_pamt(data: bytes) -> list[tuple[str, int, int, int, int]]:
    """Returns [(path, paz_offset, comp_size, orig_size, flags), ...]."""
    if len(data) < 32:
        return []
    off       = 4
    paz_count = struct.unpack_from('<I', data, off)[0]; off += 4
    if paz_count > 4096:
        return []
    off += 8
    for i in range(paz_count):
        off += 8
        if i < paz_count - 1:
            off += 4

    folder_size   = struct.unpack_from('<I', data, off)[0]; off += 4
    folder_end    = off + folder_size
    folder_prefix = ''
    tmp = off
    while tmp < folder_end:
        parent = struct.unpack_from('<I', data, tmp)[0]
        slen   = data[tmp + 4]
        name   = data[tmp + 5:tmp + 5 + slen].decode('utf-8', errors='replace')
        if parent == 0xFFFFFFFF:
            folder_prefix = name
        tmp += 5 + slen
    off = folder_end

    node_size  = struct.unpack_from('<I', data, off)[0]; off += 4
    node_start = off
    nodes: dict[int, tuple[int, str]] = {}
    while off < node_start + node_size:
        rel    = off - node_start
        parent = struct.unpack_from('<I', data, off)[0]
        slen   = data[off + 4]
        name   = data[off + 5:off + 5 + slen].decode('utf-8', errors='replace')
        nodes[rel] = (parent, name)
        off += 5 + slen

    def _build_path(node_ref: int) -> str:
        parts: list[str] = []
        cur = node_ref
        while cur != 0xFFFFFFFF and len(parts) < 64:
            if cur not in nodes:
                break
            p, n = nodes[cur]
            parts.append(n)
            cur = p
        return ''.join(reversed(parts))

    folder_count = struct.unpack_from('<I', data, off)[0]; off += 4
    off += folder_count * 16

    file_count = struct.unpack_from('<I', data, off)[0]; off += 4
    entries: list[tuple[str, int, int, int, int]] = []
    while off + 20 <= len(data):
        node_ref, paz_off, comp_size, orig_size, flags = struct.unpack_from('<IIIII', data, off)
        off += 20
        node_path = _build_path(node_ref)
        full_path = f"{folder_prefix}/{node_path}" if folder_prefix else node_path
        entries.append((full_path, paz_off, comp_size, orig_size, flags))
    return entries


def _decompress(raw: bytes, comp_type: int, orig_size: int) -> bytes | None:
    if comp_type == 0 or len(raw) == orig_size:
        return raw
    if comp_type == 2:
        if not _HAS_LZ4:
            raise RuntimeError("lz4 required: pip install lz4")
        return _lz4.decompress(raw, uncompressed_size=orig_size)
    return None


@functools.lru_cache(maxsize=256)
def find_game_path(game_dir: Path, filename: str) -> str | None:
    """Returns the canonical path of a file in the vanilla archives.

    Uses dmm_parser.parse_pamt_bytes if available (vanilla CD format),
    otherwise our own _parse_pamt (format of overlays created by the manager).
    """
    target = filename.replace('\\', '/').split('/')[-1].lower()
    dmm    = _get_dmm()
    for num in range(VANILLA_MAX + 1):
        overlay   = game_dir / f"{num:04d}"
        pamt_path = overlay / '0.pamt'
        if not pamt_path.is_file():
            continue
        try:
            raw = pamt_path.read_bytes()
            if dmm is not None:
                pamt = dmm.parse_pamt_bytes(raw)
                for directory in pamt.get('directories', []):
                    dir_path = directory.get('path', '')
                    for fentry in directory.get('files', []):
                        if fentry.get('name', '').lower() == target:
                            name = fentry['name']
                            return f"{dir_path}/{name}" if dir_path else name
            else:
                for path, *_ in _parse_pamt(raw):
                    if path.replace('\\', '/').split('/')[-1].lower() == target:
                        return path.replace('\\', '/')
        except Exception:
            continue
    return None


def extract_file(game_dir: Path, file_path: str,
                 overlay_hint: int | None = None) -> bytes | None:
    """Extracts and decompresses a file from vanilla overlays (0000–0035).

    file_path: 'gamedata/iteminfo.pabgb' or just 'iteminfo.pabgb'.
    overlay_hint: limits the search to that overlay.
    """
    norm       = file_path.replace('\\', '/')
    parts      = norm.rsplit('/', 1)
    dir_path   = parts[0] if len(parts) > 1 else ''
    file_name  = parts[-1]
    scan_range = ([overlay_hint] if overlay_hint is not None else range(VANILLA_MAX + 1))

    dmm = _get_dmm()
    if dmm is not None:
        # find_game_path resolves the exact path (e.g. 'gamedata/binary__/client/bin/inventory.pabgb')
        # that dmm.extract_file requires to match the directory in the PAMT
        canonical = find_game_path(game_dir, norm) or norm
        c_parts   = canonical.rsplit('/', 1)
        c_dir     = c_parts[0] if len(c_parts) > 1 else ''
        c_name    = c_parts[-1]
        for num in scan_range:
            group = f"{num:04d}"
            if not (game_dir / group / '0.pamt').is_file():
                continue
            try:
                result = dmm.extract_file(str(game_dir), group, c_dir, c_name)
                if result is not None:
                    return result
            except (ValueError, IOError):
                continue
        return None

    # Fallback: local PAMT parser (only used if dmm_parser is unavailable)
    target_full = norm.lower()
    target_base = target_full.split('/')[-1]
    for num in scan_range:
        overlay   = game_dir / f"{num:04d}"
        pamt_path = overlay / '0.pamt'
        paz_path  = overlay / '0.paz'
        if not pamt_path.is_file() or not paz_path.is_file():
            continue
        try:
            entries = _parse_pamt(pamt_path.read_bytes())
        except Exception as e:
            _warn(f"PAMT {num:04d} unreadable: {e}"); continue

        for path, paz_off, comp_size, orig_size, flags in entries:
            n = path.lower().replace('\\', '/')
            if n != target_full and n.split('/')[-1] != target_base:
                continue
            comp_type = (flags >> 16) & 0x0F
            try:
                with open(paz_path, 'rb') as fh:
                    fh.seek(paz_off)
                    raw = fh.read(comp_size)
            except OSError as e:
                _warn(f"PAZ {num:04d} read error: {e}"); return None
            result = _decompress(raw, comp_type, orig_size)
            if result is None:
                _warn(f"Unsupported compression type {comp_type} for {file_path}")
                return None
            return result
    return None
