from typing import Dict

import pytest
from tests.integration.agent_registry import AgentRegistry, AgentType
from tests.integration.agent_runner import AgentRunner

from theoriq.api.v1alpha2 import AgentResponse
from theoriq.api.v1alpha2.manage import DeployedAgentManager
from theoriq.api.v1alpha2.message import Messenger
from theoriq.biscuit import TheoriqBudget
from theoriq.dialog import TextItemBlock
from theoriq.types import SourceType


def is_owned_by_agent(agent: AgentResponse) -> bool:
    source_type = SourceType.from_address(agent.system.owner_address)
    return source_type.is_agent


@pytest.fixture()
def parent_manager(agent_registry: AgentRegistry) -> DeployedAgentManager:
    parent_agent_data = agent_registry.get_agents_of_type(AgentType.PARENT)[0]
    return DeployedAgentManager.from_env(env_prefix=parent_agent_data.metadata.labels["env_prefix"])


@pytest.fixture()
def parent_messenger(agent_registry: AgentRegistry) -> Messenger:
    parent_agent_data = agent_registry.get_agents_of_type(AgentType.PARENT)[0]
    return Messenger.from_env(env_prefix=parent_agent_data.metadata.labels["env_prefix"])


@pytest.mark.order(1)
@pytest.mark.usefixtures("agent_flask_apps")
def test_registration_parent(
    agent_registry: AgentRegistry, agent_map: Dict[str, AgentResponse], user_manager: DeployedAgentManager
) -> None:
    parent_agent_data = agent_registry.get_agents_of_type(AgentType.PARENT)[0]
    agent = user_manager.create_agent(parent_agent_data.spec.metadata, parent_agent_data.spec.configuration)
    agent_map[agent.system.id] = agent


@pytest.mark.order(2)
@pytest.mark.usefixtures("agent_flask_apps")
def test_registration_children(
    agent_registry: AgentRegistry, agent_map: Dict[str, AgentResponse], parent_manager: DeployedAgentManager
) -> None:
    for child_agent_data in agent_registry.get_agents_of_type(AgentType.CHILD):
        agent = parent_manager.create_agent(child_agent_data.spec.metadata, child_agent_data.spec.configuration)
        agent_map[agent.system.id] = agent


@pytest.mark.order(3)
@pytest.mark.usefixtures("agent_flask_apps")
def test_messenger(agent_map: Dict[str, AgentResponse], parent_messenger: Messenger) -> None:
    # messaging from children to parent doesn't work because minting functionality is not implemented
    # so testing parent-to-all instead of all-to-all

    for receiver_id, receiver in agent_map.items():
        message = "Hello from Parent Agent"
        blocks = [TextItemBlock(message)]
        response = parent_messenger.send_request(blocks=blocks, budget=TheoriqBudget.empty(), to_addr=receiver_id)
        actual = response.body.extract_last_text()
        expected = AgentRunner.get_echo_execute_output(message=message, agent_name=receiver.metadata.name)
        assert actual == expected


@pytest.mark.order(-2)
@pytest.mark.usefixtures("agent_flask_apps")
def test_deletion_children(agent_map: Dict[str, AgentResponse], parent_manager: DeployedAgentManager) -> None:
    children = [agent for agent in agent_map.values() if is_owned_by_agent(agent)]
    for child_agent in children:
        parent_manager.delete_agent(child_agent.system.id)

    for child_agent in children:
        del agent_map[child_agent.system.id]


@pytest.mark.order(-1)
@pytest.mark.usefixtures("agent_flask_apps")
def test_deletion_parent(agent_map: Dict[str, AgentResponse], user_manager: DeployedAgentManager) -> None:
    for agent in agent_map.values():  # should be the only one in the map
        user_manager.delete_agent(agent.system.id)
