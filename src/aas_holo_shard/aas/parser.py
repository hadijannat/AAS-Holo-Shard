"""Helpers for working with AASX packages."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Tuple, Union

from aas_holo_shard.core import shamir


def read_aasx_bytes(path: Union[str, Path]) -> bytes:
    """Read an AASX package as raw bytes."""
    return Path(path).read_bytes()


def write_aasx_bytes(path: Union[str, Path], payload: bytes) -> None:
    """Write raw bytes to an AASX package path."""
    Path(path).write_bytes(payload)


def encrypt_aasx_path(
    input_path: Union[str, Path],
    *,
    threshold: int,
    total: int,
) -> tuple[bytes, list[shamir.Share]]:
    """Encrypt an AASX file and split the key into shares."""
    aas_bytes = read_aasx_bytes(input_path)
    return shamir.encrypt_and_split(aas_bytes, threshold=threshold, total=total)


def _require_basyx() -> Tuple[Any, Any, Any, Any]:
    try:
        from basyx.aas.adapter.aasx import AASXReader, AASXWriter
        from basyx.aas.model import DictObjectStore

        try:
            from basyx.aas.adapter.aasx import DictSupplementaryFileContainer
        except Exception:  # pragma: no cover - depends on basyx version
            from basyx.aas.model import DictSupplementaryFileContainer

        return AASXReader, AASXWriter, DictObjectStore, DictSupplementaryFileContainer
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "BaSyx SDK is required for structured AASX parsing. "
            "Install the BaSyx Python SDK and ensure its AASX adapter is available."
        ) from exc


def load_aasx_basyx(path: Union[str, Path]):
    """Load an AASX package into BaSyx object and file stores."""
    AASXReader, _, DictObjectStore, DictSupplementaryFileContainer = _require_basyx()

    object_store = DictObjectStore()
    file_store = DictSupplementaryFileContainer()

    with AASXReader(str(path)) as reader:
        reader.read_into(object_store, file_store)

    return object_store, file_store
