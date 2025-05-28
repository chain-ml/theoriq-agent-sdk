from copy import deepcopy
from typing import Dict

import pytest
from tests.integration.agent_registry import AgentRegistry, AgentType
from tests.integration.agent_runner import AgentRunner
from tests.integration.utils import agents_are_equal

from theoriq import AgentDeploymentConfiguration
from theoriq.api.v1alpha2 import AgentResponse
from theoriq.api.v1alpha2.manage import DeployedAgentManager
from theoriq.api.v1alpha2.message import Messenger
from theoriq.biscuit import TheoriqBudget
from theoriq.dialog import TextItemBlock


@pytest.mark.order(1)
@pytest.mark.usefixtures("agent_flask_apps")
def test_registration(
    agent_registry: AgentRegistry, agent_map: Dict[str, AgentResponse], user_manager: DeployedAgentManager
) -> None:
    agents = agent_registry.get_agents_of_type(AgentType.PARENT) + agent_registry.get_agents_of_type(AgentType.CHILD)
    for agent_data in agents:
        agent = user_manager.create_agent(
            metadata=agent_data.spec.metadata, configuration=agent_data.spec.configuration
        )
        print(f"Successfully registered `{agent.metadata.name}` with id=`{agent.system.id}`\n")
        agent_map[agent.system.id] = agent


@pytest.mark.order(2)
@pytest.mark.usefixtures("agent_flask_apps")
def test_minting(agent_map: Dict[str, AgentResponse], user_manager: DeployedAgentManager) -> None:
    for agent_id in agent_map.keys():
        agent = user_manager.mint_agent(agent_id)
        assert agent.system.state == "online"
        print(f"Successfully minted `{agent_id}`\n")


@pytest.mark.order(3)
@pytest.mark.usefixtures("agent_flask_apps")
def test_get_agents(agent_map: Dict[str, AgentResponse], user_manager: DeployedAgentManager) -> None:
    agents = user_manager.get_agents()
    assert len(agents) >= len(agent_map.keys())
    fetched_agents: Dict[str, AgentResponse] = {agent.system.id: agent for agent in agents}

    for agent in agent_map.values():
        assert agent.system.id in fetched_agents
        assert agents_are_equal(agent, fetched_agents[agent.system.id])

        same_agent = user_manager.get_agent(agent.system.id)
        assert agents_are_equal(agent, same_agent)


@pytest.mark.order(4)
@pytest.mark.usefixtures("agent_flask_apps")
def test_unminting(agent_map: Dict[str, AgentResponse], user_manager: DeployedAgentManager) -> None:
    for agent_id in agent_map.keys():
        agent = user_manager.unmint_agent(agent_id)
        assert agent.system.state == "configured"
        print(f"Successfully unminted `{agent_id}`\n")


@pytest.mark.order(5)
@pytest.mark.usefixtures("agent_flask_apps")
def test_messenger(agent_map: Dict[str, AgentResponse], user_messenger: Messenger) -> None:
    message = "Hello from user"
    blocks = [TextItemBlock(message)]

    for agent_id, agent in agent_map.items():
        response = user_messenger.send_request(blocks=blocks, budget=TheoriqBudget.empty(), to_addr=agent_id)
        assert response.body.extract_last_text() == AgentRunner.get_echo_execute_output(
            message=message, agent_name=agent.metadata.name
        )


@pytest.mark.order(6)
@pytest.mark.usefixtures("agent_flask_apps")
def test_updating(agent_registry: AgentRegistry, user_manager: DeployedAgentManager) -> None:
    parent_agent_data = agent_registry.get_agents_of_type(AgentType.PARENT)[0]
    updated_agent_data = deepcopy(parent_agent_data)
    updated_agent_data.spec.metadata.name = "Updated Parent Agent"

    config = AgentDeploymentConfiguration.from_env(env_prefix=parent_agent_data.metadata.labels["env_prefix"])

    response = user_manager.update_agent(agent_id=str(config.address), metadata=updated_agent_data.spec.metadata)

    assert response.metadata.name == "Updated Parent Agent"


@pytest.mark.order(-1)
@pytest.mark.usefixtures("agent_flask_apps")
def test_deletion(agent_map: Dict[str, AgentResponse], user_manager: DeployedAgentManager) -> None:
    for agent in agent_map.values():
        user_manager.delete_agent(agent.system.id)
        print(f"Successfully deleted `{agent.system.id}`\n")
