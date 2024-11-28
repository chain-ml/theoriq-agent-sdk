import pytest

from theoriq.biscuit import PayloadHash


def test_equality():
    payload = "Theoriq SDK helps to develop agent on top of Theoriq Protocol"
    payload_bytes = payload.encode("utf-8")
    ph = PayloadHash(payload=payload_bytes)

    assert ph == PayloadHash.from_str(payload)

    ph_str = f"{ph}"
    assert ph == ph_str
    assert ph == ph_str.removeprefix("0x")
    assert ph == ph_str.upper()
    assert ph == ph_str.lower()

    hash_value = "d3c3945ef8015911102145011bb2b2d3bb31bd784aa8b19b38ad168a92777a15"
    assert ph == PayloadHash.from_hash(hash_value)
    assert ph == PayloadHash.from_hash(f"0x{hash_value}")
    assert ph == PayloadHash.from_hash(f"0x{hash_value.upper()}")
    assert ph == PayloadHash.from_hash(f"{hash_value.upper()}")


def test_inequality():
    payload = "Theoriq SDK helps to develop agent on top of Theoriq Protocol"
    payload_bytes = payload.encode("utf-8")
    ph = PayloadHash(payload=payload_bytes)

    assert ph != PayloadHash.from_str(payload.upper())


def test_invalid_hash():
    with pytest.raises(ValueError):
        PayloadHash.from_hash("0x")

    with pytest.raises(ValueError):
        PayloadHash.from_hash("z3c3945ef8015911102145011bb2b2d3bb31bd784aa8b19b38ad168a92777a15")
