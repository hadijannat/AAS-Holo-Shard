import pytest
from hypothesis import given, strategies as st

from aas_holo_shard.core import shamir


@given(st.binary(min_size=1, max_size=2048))
def test_encrypt_split_roundtrip(data: bytes) -> None:
    encrypted, shares = shamir.encrypt_and_split(data, threshold=3, total=5)
    recovered = shamir.reconstruct_and_decrypt(encrypted, shares[:3])
    assert recovered == data


@given(
    st.binary(min_size=1, max_size=512),
    st.lists(st.integers(min_value=0, max_value=3), min_size=2, max_size=2, unique=True),
)
def test_any_threshold_subset(data: bytes, indices: list[int]) -> None:
    encrypted, shares = shamir.encrypt_and_split(data, threshold=2, total=4)
    subset = [shares[i] for i in indices]
    recovered = shamir.reconstruct_and_decrypt(encrypted, subset)
    assert recovered == data


def test_invalid_thresholds() -> None:
    with pytest.raises(shamir.CryptoError):
        shamir.encrypt_and_split(b"test", threshold=0, total=3)
    with pytest.raises(shamir.CryptoError):
        shamir.encrypt_and_split(b"test", threshold=4, total=3)


def test_invalid_share_length() -> None:
    encrypted, shares = shamir.encrypt_and_split(b"hello", threshold=2, total=3)
    bad_shares = [(shares[0][0], shares[0][1][:8])]
    with pytest.raises(shamir.CryptoError):
        shamir.reconstruct_and_decrypt(encrypted, bad_shares)
