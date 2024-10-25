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

def test_inequality():
    payload = "Theoriq SDK helps to develop agent on top of Theoriq Protocol"
    payload_bytes = payload.encode("utf-8")
    ph = PayloadHash(payload=payload_bytes)

    assert ph != PayloadHash.from_str(payload.upper())
