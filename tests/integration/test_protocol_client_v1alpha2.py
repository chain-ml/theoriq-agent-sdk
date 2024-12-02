from theoriq.api import AgentResponseV1alpha2, ProtocolClientV1alpha2


def test_get_agent():
    pc = ProtocolClientV1alpha2("http://localhost:8080")
    agent = pc.get_agent("0x75ee7a59a024d9b5e4b3ee6b9784d53e36456650677221a7f56ce4a91b93a9d8")
    assert isinstance(agent, AgentResponseV1alpha2)


def test_get_agents():
    pc = ProtocolClientV1alpha2("http://localhost:8080")
    agents = pc.get_agents()

    assert len(agents) > 0
    for agent in agents:
        assert isinstance(agent, AgentResponseV1alpha2)


def test_get_public_key():
    pc = ProtocolClientV1alpha2("http://localhost:8080")
    pub_key = pc.get_public_key()
    assert pub_key.key_type == "ed25519"
