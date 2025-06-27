from theoriq.api.v1alpha2 import ProtocolClient


def test_get_public_key():
    pc = ProtocolClient("http://localhost:8080")
    pub_key = pc.get_public_key()
    assert pub_key.key_type == "ed25519"
