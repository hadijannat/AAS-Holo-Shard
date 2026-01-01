import json

import pytest

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


def test_make_shards_invalid_inputs() -> None:
    with pytest.raises(ValueError):
        shard.make_shards(1, n=0, k=1)
    with pytest.raises(ValueError):
        shard.make_shards(1, n=1, k=2)
    with pytest.raises(ValueError):
        shard.make_shards(shard.PRIME, n=2, k=1)


def test_recover_secret_requires_shards() -> None:
    with pytest.raises(ValueError):
        shard.recover_secret([])


def test_parse_shard_value() -> None:
    assert shard._parse_shard_value("NOPE") is None
    assert shard._parse_shard_value("SHARD_V1:1") is None
    valid = shard._parse_shard_value("SHARD_V1:1:2")
    assert valid == (1, 2)


def test_int_to_str_zero() -> None:
    assert shard.int_to_str(0) == ""


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


def test_split_missing_target(tmp_path) -> None:
    source = tmp_path / "factory.json"
    source.write_text(json.dumps(_make_sample()))
    with pytest.raises(ValueError):
        shard.split_aas(source, "MissingKey", n=2, k=2)


def test_split_secret_too_long(tmp_path) -> None:
    sample = _make_sample()
    sample["submodels"][0]["submodelElements"][0]["value"] = "A" * 100
    source = tmp_path / "factory.json"
    source.write_text(json.dumps(sample))
    with pytest.raises(ValueError):
        shard.split_aas(source, "MasterKey", n=2, k=2)


def test_combine_requires_shards(tmp_path) -> None:
    source = tmp_path / "factory.json"
    source.write_text(json.dumps(_make_sample()))
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(_make_sample()))
    with pytest.raises(ValueError):
        shard.combine_aas([bad], "MasterKey", tmp_path / "restored.json")


def test_combine_invalid_utf8(tmp_path) -> None:
    sample = _make_sample()
    source = tmp_path / "factory.json"
    source.write_text(json.dumps(sample))

    shards = shard.make_shards(255, n=2, k=2)
    shard_files = []
    for idx, shard_data in enumerate(shards, start=1):
        shard_doc = json.loads(source.read_text())
        elem = shard.find_element(shard_doc, "MasterKey")
        assert elem is not None
        shard._inject_shard_value(elem, shard_data)
        out_path = tmp_path / f"shard_{idx}.json"
        out_path.write_text(json.dumps(shard_doc))
        shard_files.append(out_path)

    with pytest.raises(ValueError):
        shard.combine_aas(shard_files, "MasterKey", tmp_path / "restored.json")


def test_main_split_and_combine(tmp_path, capsys) -> None:
    source = tmp_path / "factory.json"
    source.write_text(json.dumps(_make_sample()))

    assert shard.main(["split", str(source), "MasterKey", "-n", "2", "-k", "2"]) == 0
    assert shard.main(
        [
            "combine",
            "MasterKey",
            str(tmp_path / "factory_shard_1.json"),
            str(tmp_path / "factory_shard_2.json"),
            "-o",
            str(tmp_path / "restored.json"),
        ]
    ) == 0

    captured = capsys.readouterr()
    assert "Reconstruction successful" in captured.out


def test_main_error_path(capsys) -> None:
    assert shard.main(["combine", "Missing", "missing.json"]) == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err
