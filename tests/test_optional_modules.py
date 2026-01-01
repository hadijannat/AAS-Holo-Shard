import json
import sys
import types

import pytest

from aas_holo_shard.aas import parser
from aas_holo_shard.storage import ipfs


def test_read_write_bytes(tmp_path) -> None:
    path = tmp_path / "sample.aasx"
    parser.write_aasx_bytes(path, b"hello")
    assert parser.read_aasx_bytes(path) == b"hello"


def test_encrypt_aasx_path(tmp_path) -> None:
    path = tmp_path / "sample.aasx"
    parser.write_aasx_bytes(path, b"payload")
    encrypted, shares = parser.encrypt_aasx_path(path, threshold=2, total=3)
    assert encrypted
    assert len(shares) == 3


def test_basyx_dummy_modules(monkeypatch, tmp_path) -> None:
    adapter = types.ModuleType("basyx.aas.adapter")
    adapter_aasx = types.ModuleType("basyx.aas.adapter.aasx")
    model = types.ModuleType("basyx.aas.model")

    class DummyReader:
        def __init__(self, path):
            self.path = path

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read_into(self, object_store, file_store):
            object_store["read"] = True
            file_store["read"] = True

    class DummyWriter:
        pass

    class DictObjectStore(dict):
        pass

    class DictSupplementaryFileContainer(dict):
        pass

    adapter_aasx.AASXReader = DummyReader
    adapter_aasx.AASXWriter = DummyWriter
    adapter_aasx.DictSupplementaryFileContainer = DictSupplementaryFileContainer
    model.DictObjectStore = DictObjectStore
    model.DictSupplementaryFileContainer = DictSupplementaryFileContainer

    monkeypatch.setitem(sys.modules, "basyx", types.ModuleType("basyx"))
    monkeypatch.setitem(sys.modules, "basyx.aas", types.ModuleType("basyx.aas"))
    monkeypatch.setitem(sys.modules, "basyx.aas.adapter", adapter)
    monkeypatch.setitem(sys.modules, "basyx.aas.adapter.aasx", adapter_aasx)
    monkeypatch.setitem(sys.modules, "basyx.aas.model", model)

    object_store, file_store = parser.load_aasx_basyx(tmp_path / "dummy.aasx")
    assert object_store.get("read") is True
    assert file_store.get("read") is True


def test_ipfs_roundtrip_with_dummy_client() -> None:
    class DummyClient:
        def __init__(self):
            self.store = {}

        def add_bytes(self, payload: bytes) -> str:
            cid = f"cid-{len(self.store)}"
            self.store[cid] = payload
            return cid

        def cat(self, cid: str) -> bytes:
            return self.store[cid]

    client = DummyClient()
    shares = [(1, b"abc"), (2, b"def")]
    cids = ipfs.store_shares(shares, client=client)
    fetched = ipfs.fetch_shares(cids, client=client)
    assert fetched == shares


def test_ipfs_serialize_deserialize() -> None:
    share = (7, b"payload")
    payload = ipfs.serialize_share(share)
    assert ipfs.deserialize_share(payload) == share


def test_ipfs_get_client_with_dummy_module(monkeypatch) -> None:
    class DummyClient:
        def __init__(self):
            self.connected = True

    dummy_module = types.ModuleType("ipfshttpclient")

    def connect():
        return DummyClient()

    dummy_module.connect = connect
    monkeypatch.setitem(sys.modules, "ipfshttpclient", dummy_module)

    client = ipfs._get_client()
    assert hasattr(client, "connected")
