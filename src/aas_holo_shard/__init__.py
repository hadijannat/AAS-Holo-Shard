"""AAS-Holo-Shard package."""

from aas_holo_shard.core.shamir import (
    CryptoError,
    Share,
    encrypt_and_split,
    reconstruct_and_decrypt,
)

__all__ = [
    "CryptoError",
    "Share",
    "encrypt_and_split",
    "reconstruct_and_decrypt",
]

__version__ = "0.1.0"
