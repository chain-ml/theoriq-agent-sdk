from biscuit_auth import PublicKey

from theoriq.biscuit import AgentAddress


def test_agent_address_from_public_key():
    pub_key = PublicKey.from_hex("81d0ff760a8a2a5b3da3d942deef217fdbefe00e36106052f9194661c234777c")
    agent_address = AgentAddress.from_public_key(pub_key)

    assert str(agent_address) == "d55659c9b3843dcaf36ab2b8579aafed5459bee83777615ca00b1bed938fb3bf"
