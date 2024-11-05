from theoriq import ProtocolClientV1, ProtocolClientV2
from theoriq.api_v1alpha2.schemas import AgentResponse

def test_get_agents():
    pc = ProtocolClientV2("http://localhost:8080")
    agents = pc.get_agents()

    assert len(agents) > 0
    for agent in agents:
        assert isinstance(agent, AgentResponse)


def test_get_public_key():
    pc = ProtocolClientV1("http://localhost:8080")
    pub_key = pc.get_public_key()
    assert pub_key.key_type == "ed25519"
