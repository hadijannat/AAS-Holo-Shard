"""IPFS storage helpers for share payloads."""

from __future__ import annotations

import base64
import json
from typing import Iterable, List, Optional

from aas_holo_shard.core.shamir import Share


class IPFSUnavailable(RuntimeError):
    """Raised when IPFS client is unavailable or misconfigured."""


def _get_client(client=None):
    if client is not None:
        return client

    try:
        import ipfshttpclient  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        raise IPFSUnavailable("ipfshttpclient is not installed") from exc

    try:
        return ipfshttpclient.connect()
    except Exception as exc:  # pragma: no cover - environment-specific
        raise IPFSUnavailable("unable to connect to local IPFS daemon") from exc


def serialize_share(share: Share) -> bytes:
    idx, payload = share
    data = {
        "index": int(idx),
        "payload": base64.b64encode(payload).decode("ascii"),
    }
    return json.dumps(data, separators=(",", ":")).encode("utf-8")


def deserialize_share(payload: bytes) -> Share:
    data = json.loads(payload.decode("utf-8"))
    return int(data["index"]), base64.b64decode(data["payload"])


def store_shares(shares: Iterable[Share], client=None) -> List[str]:
    ipfs = _get_client(client)
    cids: List[str] = []
    for share in shares:
        cid = ipfs.add_bytes(serialize_share(share))
        cids.append(cid)
    return cids


def fetch_shares(cids: Iterable[str], client=None) -> List[Share]:
    ipfs = _get_client(client)
    shares: List[Share] = []
    for cid in cids:
        payload = ipfs.cat(cid)
        shares.append(deserialize_share(payload))
    return shares

