from theoriq.api import ProtocolClientV1alpha2


def test_get_public_key():
    pc = ProtocolClientV1alpha2("http://localhost:8080")
    pub_key = pc.get_public_key()
    assert pub_key.key_type == "ed25519"
