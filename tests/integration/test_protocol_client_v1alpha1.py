from theoriq.api import AgentResponseV1alpha1, ProtocolClientV1alpha1


def test_get_agent():
    pc = ProtocolClientV1alpha1("https://infinity.theoriq.ai")
    agent = pc.get_agent("d1d0a2284fac534d360d741a504928f15c994aeb339c2c498f68057baa628b4c")
    assert isinstance(agent, AgentResponseV1alpha1)


def test_get_agents():
    pc = ProtocolClientV1alpha1("http://localhost:8080")
    agents = pc.get_agents()

    assert len(agents) > 0
    for agent in agents:
        assert isinstance(agent, AgentResponseV1alpha1)


def test_get_public_key():
    pc = ProtocolClientV1alpha1("https://infinity.theoriq.ai")
    pub_key = pc.get_public_key()
    assert pub_key.key_type == "ed25519"


def test_cached_public_key():
    pc = ProtocolClientV1alpha1("https://infinity.theoriq.ai")
    pub_key = pc.public_key
    assert pub_key.startswith("0x")

    pc = ProtocolClientV1alpha1("https://infinity.theoriq.ai")
    pub_key = pc.public_key
    assert pub_key.startswith("0x")
