from theoriq.api import AgentResponseV1alpha1, AgentResponseV1alpha2, ProtocolClientV1alpha1, ProtocolClientV1alpha2


def test_get_agent():
    pc = ProtocolClientV1alpha1("http://localhost:8080")
    agent = pc.get_agent("110b06ec141df9f1e147a1a2de446c302786d7a2e991a715b33d64a7f993e025")
    assert isinstance(agent, AgentResponseV1alpha1)


def test_get_agents():
    pc = ProtocolClientV1alpha2("http://localhost:8080")
    agents = pc.get_agents()

    assert len(agents) > 0
    for agent in agents:
        assert isinstance(agent, AgentResponseV1alpha2)


def test_get_public_key():
    pc = ProtocolClientV1alpha1("http://localhost:8080")
    pub_key = pc.get_public_key()
    assert pub_key.key_type == "ed25519"
