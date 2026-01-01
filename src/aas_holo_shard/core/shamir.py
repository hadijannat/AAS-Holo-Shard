"""Shamir-based key splitting for AASX encryption."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple

try:
    from Crypto.Cipher import AES
    from Crypto.Protocol.SecretSharing import Shamir
    from Crypto.Random import get_random_bytes
except Exception as exc:  # pragma: no cover - handled at import time
    raise RuntimeError(
        "pycryptodome is required for aas_holo_shard.core.shamir"
    ) from exc

MAGIC = b"AHS1"
KEY_SIZE = 32
HALF_KEY = 16
NONCE_SIZE = 16
TAG_SIZE = 16

Share = Tuple[int, bytes]


class CryptoError(ValueError):
    """Raised when cryptographic inputs are invalid or unsupported."""


def _validate_thresholds(threshold: int, total: int) -> None:
    if threshold < 1:
        raise CryptoError("threshold must be >= 1")
    if total < 1:
        raise CryptoError("total shares must be >= 1")
    if threshold > total:
        raise CryptoError("threshold cannot be greater than total shares")
    if total > 255:
        raise CryptoError("total shares must be <= 255 for Shamir indices")


def _split_key(key: bytes, threshold: int, total: int) -> List[Share]:
    if len(key) != KEY_SIZE:
        raise CryptoError(f"key must be {KEY_SIZE} bytes")
    _validate_thresholds(threshold, total)

    shares_1 = Shamir.split(threshold, total, key[:HALF_KEY])
    shares_2 = Shamir.split(threshold, total, key[HALF_KEY:])

    combined: List[Share] = []
    for (idx, part_1), (_, part_2) in zip(shares_1, shares_2):
        combined.append((idx, part_1 + part_2))
    return combined


def _combine_key(shares: Iterable[Share]) -> bytes:
    share_list = list(shares)
    if not share_list:
        raise CryptoError("at least one share is required")

    for idx, payload in share_list:
        if not isinstance(idx, int):
            raise CryptoError("share index must be an int")
        if len(payload) != KEY_SIZE:
            raise CryptoError("share payload must be 32 bytes")

    shares_1 = [(idx, payload[:HALF_KEY]) for idx, payload in share_list]
    shares_2 = [(idx, payload[HALF_KEY:]) for idx, payload in share_list]

    key_1 = Shamir.combine(shares_1)
    key_2 = Shamir.combine(shares_2)
    return key_1 + key_2


def _pack_encrypted(nonce: bytes, tag: bytes, ciphertext: bytes) -> bytes:
    if len(nonce) != NONCE_SIZE:
        raise CryptoError(f"nonce must be {NONCE_SIZE} bytes")
    if len(tag) != TAG_SIZE:
        raise CryptoError(f"tag must be {TAG_SIZE} bytes")
    return MAGIC + nonce + tag + ciphertext


def _unpack_encrypted(blob: bytes) -> tuple[bytes, bytes, bytes]:
    header_len = len(MAGIC) + NONCE_SIZE + TAG_SIZE
    if len(blob) < header_len:
        raise CryptoError("encrypted payload is too short")
    if not blob.startswith(MAGIC):
        raise CryptoError("encrypted payload missing magic header")

    offset = len(MAGIC)
    nonce = blob[offset : offset + NONCE_SIZE]
    offset += NONCE_SIZE
    tag = blob[offset : offset + TAG_SIZE]
    offset += TAG_SIZE
    ciphertext = blob[offset:]
    return nonce, tag, ciphertext


def encrypt_and_split(
    aas_bytes: bytes,
    *,
    threshold: int,
    total: int,
) -> tuple[bytes, List[Share]]:
    """Encrypt AAS bytes and split the encryption key into shares."""
    _validate_thresholds(threshold, total)

    key = get_random_bytes(KEY_SIZE)
    nonce = get_random_bytes(NONCE_SIZE)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(aas_bytes)

    encrypted = _pack_encrypted(cipher.nonce, tag, ciphertext)
    shares = _split_key(key, threshold, total)
    return encrypted, shares


def reconstruct_and_decrypt(
    encrypted: bytes, shares: Iterable[Share]
) -> bytes:
    """Reconstruct the encryption key from shares and decrypt payload."""
    key = _combine_key(shares)
    nonce, tag, ciphertext = _unpack_encrypted(encrypted)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)


@dataclass(frozen=True)
class EncryptedBundle:
    """Container for encrypted bytes plus the share list."""

    encrypted: bytes
    shares: List[Share]

    def to_dict(self) -> dict:
        return {
            "encrypted": self.encrypted,
            "shares": self.shares,
        }
