from theoriq.protocol.protocol_client import ProtocolClient


def test_get_agents():
    pc = ProtocolClient("https://ap-backend.dev-02.lab.chainml.net")
    agents = pc.get_agents()
    assert len(agents) > 0

    print()
    [print(agent) for agent in agents]


def test_get_public_key():
    pc = ProtocolClient("https://ap-backend.dev-02.lab.chainml.net")
    pub_key = pc.get_public_key()
    assert pub_key.key_type == "ed25519"
