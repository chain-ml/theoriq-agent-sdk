from theoriq.api.v1alpha2 import AgentResponse, ProtocolClient
from theoriq.api.v1alpha2.manage import DeployedAgentManager


def test_get_agents_with_client() -> None:
    client = ProtocolClient.from_env()
    agents = client.get_agents()
    assert len(agents) > 0  # require at least one minted agent

    for agent in agents:
        assert isinstance(agent, AgentResponse)
        assert agent.configuration.is_empty


def test_get_agents_with_manager(user_manager: DeployedAgentManager) -> None:
    user_address = user_manager._biscuit_provider.address

    agents = user_manager.get_agents()
    assert len(agents) > 0

    for agent in agents:
        if agent.system.owner_address == user_address:
            agent_private = user_manager.get_agent(agent.system.id)
            assert agent_private.configuration.is_valid
