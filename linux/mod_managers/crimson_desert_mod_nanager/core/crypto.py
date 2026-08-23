"""Cryptographic primitives — Bob Jenkins hashlittle + ChaCha20."""

import os
import struct
from pathlib import Path

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
    _HAS_CRYPTO = True
except ImportError:
    _HAS_CRYPTO = False

# ── Constants ─────────────────────────────────────────────────────────────────

HASH_SEED     = 0xC5EDE
IV_XOR        = 0x60616263
XOR_DELTAS    = [0x00000000, 0x0A0A0A0A, 0x0C0C0C0C, 0x06060606,
                 0x0E0E0E0E, 0x0A0A0A0A, 0x06060606, 0x02020202]
ENCRYPTED_EXT: set[str] = set()  # PackGroupBuilder uses Crypto.NONE — no per-file ChaCha20 in mod overlays


# ── Bob Jenkins hashlittle ────────────────────────────────────────────────────

def _rot32(x: int, k: int) -> int:
    return ((x << k) | (x >> (32 - k))) & 0xFFFFFFFF


def _mix(a: int, b: int, c: int) -> tuple[int, int, int]:
    a = (a - c) & 0xFFFFFFFF; a ^= _rot32(c,  4); c = (c + b) & 0xFFFFFFFF
    b = (b - a) & 0xFFFFFFFF; b ^= _rot32(a,  6); a = (a + c) & 0xFFFFFFFF
    c = (c - b) & 0xFFFFFFFF; c ^= _rot32(b,  8); b = (b + a) & 0xFFFFFFFF
    a = (a - c) & 0xFFFFFFFF; a ^= _rot32(c, 16); c = (c + b) & 0xFFFFFFFF
    b = (b - a) & 0xFFFFFFFF; b ^= _rot32(a, 19); a = (a + c) & 0xFFFFFFFF
    c = (c - b) & 0xFFFFFFFF; c ^= _rot32(b,  4); b = (b + a) & 0xFFFFFFFF
    return a, b, c


def _final(a: int, b: int, c: int) -> tuple[int, int, int]:
    c ^= b; c = (c - _rot32(b, 14)) & 0xFFFFFFFF
    a ^= c; a = (a - _rot32(c, 11)) & 0xFFFFFFFF
    b ^= a; b = (b - _rot32(a, 25)) & 0xFFFFFFFF
    c ^= b; c = (c - _rot32(b, 16)) & 0xFFFFFFFF
    a ^= c; a = (a - _rot32(c,  4)) & 0xFFFFFFFF
    b ^= a; b = (b - _rot32(a, 14)) & 0xFFFFFFFF
    c ^= b; c = (c - _rot32(b, 24)) & 0xFFFFFFFF
    return a, b, c


def hashlittle(data: bytes, initval: int = 0) -> int:
    length = len(data)
    a = b = c = (0xDEADBEEF + length + initval) & 0xFFFFFFFF
    i, rem = 0, length
    while rem > 12:
        v = struct.unpack_from('<III', data, i)
        a = (a + v[0]) & 0xFFFFFFFF
        b = (b + v[1]) & 0xFFFFFFFF
        c = (c + v[2]) & 0xFFFFFFFF
        a, b, c = _mix(a, b, c)
        i += 12; rem -= 12
    tail = data[i:] + b'\x00' * 12
    v = struct.unpack_from('<III', tail)
    a = (a + v[0]) & 0xFFFFFFFF
    b = (b + v[1]) & 0xFFFFFFFF
    c = (c + v[2]) & 0xFFFFFFFF
    _, _, c = _final(a, b, c)
    return c


# ── ChaCha20 key derivation ───────────────────────────────────────────────────

def derive_key_iv(filename: str) -> tuple[bytes, bytes]:
    """Derives ChaCha20 key (32 B) and IV (16 B) from the filename."""
    basename = os.path.basename(filename).lower()
    seed     = hashlittle(basename.encode('utf-8'), HASH_SEED)
    iv       = struct.pack('<I', seed) * 4
    key_base = seed ^ IV_XOR
    key      = b''.join(struct.pack('<I', key_base ^ d) for d in XOR_DELTAS)
    return key, iv


def chacha20_encrypt(data: bytes, filename: str) -> bytes:
    """Encrypts/decrypts with ChaCha20 (symmetric operation)."""
    if not _HAS_CRYPTO:
        raise RuntimeError("Package 'cryptography' required: pip install cryptography")
    key, iv = derive_key_iv(filename)
    cipher  = Cipher(algorithms.ChaCha20(key, iv), mode=None)
    return cipher.encryptor().update(data)


def needs_encryption(filename: str) -> bool:
    return Path(filename).suffix.lower() in ENCRYPTED_EXT
