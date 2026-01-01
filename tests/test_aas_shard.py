import json

from aas_holo_shard.aas import shard


def _make_sample() -> dict:
    return {
        "assetAdministrationShells": [{"id": "urn:uuid:fac-1", "idShort": "Demo"}],
        "submodels": [
            {
                "idShort": "ProductionParams",
                "submodelElements": [
                    {
                        "idShort": "MasterKey",
                        "modelType": "Property",
                        "valueType": "xs:string",
                        "value": "TopSecretValue",
                    }
                ],
            }
        ],
    }


def test_make_and_recover_secret() -> None:
    secret = shard.str_to_int("hello")
    shares = shard.make_shards(secret, n=3, k=2)
    recovered = shard.recover_secret(shares[:2])
    assert shard.int_to_str(recovered) == "hello"


def test_split_and_combine_aas(tmp_path) -> None:
    source = tmp_path / "factory.json"
    source.write_text(json.dumps(_make_sample()))

    outputs = shard.split_aas(source, "MasterKey", n=3, k=2)
    assert len(outputs) == 3

    shard_payload = json.loads(outputs[0].read_text())
    elem = shard.find_element(shard_payload, "MasterKey")
    assert elem is not None
    assert str(elem["value"]).startswith(f"{shard.SHARD_PREFIX}:")

    recovered = shard.combine_aas(outputs[:2], "MasterKey", tmp_path / "restored.json")
    assert recovered == "TopSecretValue"

    restored = json.loads((tmp_path / "restored.json").read_text())
    restored_elem = shard.find_element(restored, "MasterKey")
    assert restored_elem is not None
    assert restored_elem["value"] == "TopSecretValue"
