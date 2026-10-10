"""Standard public cryptographic primitives.

HKDF-SHA256 implemented per RFC 5869 (verified in tests against the RFC's
Test Case 1 vector). HMAC-SHA256 from the standard library. Nothing here is
novel or restricted — this is the same key-derivation / MAC machinery used
in TLS, Signal, and ordinary IoT device authentication.
"""
import hashlib
import hmac
from . import config

_HASH = hashlib.sha256
_HASH_LEN = 32


def hkdf_extract(salt: bytes, ikm: bytes) -> bytes:
    if not salt:
        salt = b"\x00" * _HASH_LEN
    return hmac.new(salt, ikm, _HASH).digest()


def hkdf_expand(prk: bytes, info: bytes, length: int) -> bytes:
    t = b""
    okm = b""
    counter = 1
    while len(okm) < length:
        t = hmac.new(prk, t + info + bytes([counter]), _HASH).digest()
        okm += t
        counter += 1
    return okm[:length]


def hkdf(ikm: bytes, salt: bytes, info: bytes, length: int) -> bytes:
    """RFC 5869 HKDF with SHA-256."""
    return hkdf_expand(hkdf_extract(salt, ikm), info, length)


def epoch_key(master_key: bytes, epoch: int) -> bytes:
    return hkdf(master_key, b"iff-epoch", epoch.to_bytes(8, "big"), 32)


def unit_key(master_key: bytes, epoch: int, unit_id: bytes) -> bytes:
    ek = epoch_key(master_key, epoch)
    return hkdf(ek, b"iff-unit", unit_id, 32)


def iq_key(master_key: bytes, epoch: int) -> bytes:
    return hkdf(epoch_key(master_key, epoch), b"iff-iq", b"", 32)


def challenge_tag(key: bytes, nonce: bytes, interrogator_id: str, epoch: int) -> bytes:
    payload = b"CQ" + nonce + interrogator_id.encode("utf-8") + epoch.to_bytes(8, "big")
    return hmac.new(key, payload, _HASH).digest()[:4]


def response_tag(uk: bytes, nonce: bytes, unit_id: bytes, epoch: int,
                 tag_bits: int = config.TAG_BITS) -> bytes:
    """Truncated HMAC over the challenge binding (component 1)."""
    full = hmac.new(uk, b"C1" + nonce + unit_id + epoch.to_bytes(8, "big"), _HASH).digest()
    nbytes = (tag_bits + 7) // 8
    return full[:nbytes]


def maneuver_bits(uk: bytes, unit_id: bytes, window: int, n_bits: int) -> list:
    """Derive the per-window maneuver bit pattern (component 2)."""
    full = hmac.new(uk, b"C2" + unit_id + window.to_bytes(8, "big"), _HASH).digest()
    bits = []
    for i in range(n_bits):
        byte = full[i // 8]
        bit = (byte >> (7 - (i % 8))) & 1
        bits.append(bit)
    return bits
