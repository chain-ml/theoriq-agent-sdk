from typing import Dict

import pytest
from tests.integration.agent_registry import AgentRegistry, AgentType
from tests.integration.agent_runner import AgentRunner

from theoriq.api.v1alpha2 import AgentResponse
from theoriq.api.v1alpha2.manage import AgentManager
from theoriq.api.v1alpha2.message import Messenger
from theoriq.dialog import TextItemBlock
from theoriq.types import SourceType


def is_owned_by_agent(agent: AgentResponse) -> bool:
    source_type = SourceType.from_address(agent.system.owner_address)
    return source_type.is_agent


@pytest.fixture()
def owner_manager(agent_registry: AgentRegistry) -> AgentManager:
    owner_agent_data = agent_registry.get_first_agent_of_type(AgentType.OWNER)
    return AgentManager.from_env(env_prefix=owner_agent_data.metadata.labels["env_prefix"])


@pytest.fixture()
def owner_messenger(agent_registry: AgentRegistry) -> Messenger:
    owner_agent_data = agent_registry.get_first_agent_of_type(AgentType.OWNER)
    return Messenger.from_env(env_prefix=owner_agent_data.metadata.labels["env_prefix"])


@pytest.mark.order(1)
@pytest.mark.usefixtures("agent_flask_apps")
def test_registration_owner(
    agent_registry: AgentRegistry, agent_map: Dict[str, AgentResponse], user_manager: AgentManager
) -> None:
    owner_agent_data = agent_registry.get_first_agent_of_type(AgentType.OWNER)
    agent = user_manager.create_agent(owner_agent_data.spec.metadata, owner_agent_data.spec.configuration)
    agent_map[agent.system.id] = agent


@pytest.mark.order(2)
@pytest.mark.usefixtures("agent_flask_apps")
def test_registration_basic(
    agent_registry: AgentRegistry, agent_map: Dict[str, AgentResponse], owner_manager: AgentManager
) -> None:
    for basic_agent_data in agent_registry.get_agents_of_type(AgentType.BASIC):
        agent = owner_manager.create_agent(basic_agent_data.spec.metadata, basic_agent_data.spec.configuration)
        agent_map[agent.system.id] = agent


@pytest.mark.order(3)
@pytest.mark.usefixtures("agent_flask_apps")
def test_messenger(agent_map: Dict[str, AgentResponse], owner_messenger: Messenger) -> None:
    # messaging from basic to owner doesn't work because minting functionality is not implemented
    # so testing owner-to-all instead of all-to-all

    for receiver_id, receiver in agent_map.items():
        message = "Hello from Parent Agent"
        blocks = [TextItemBlock(message)]
        response = owner_messenger.send_request(blocks=blocks, to_addr=receiver_id)
        actual = response.body.extract_last_text()
        expected = AgentRunner.get_echo_execute_output(message=message, agent_name=receiver.metadata.name)
        assert actual == expected


@pytest.mark.order(-2)
@pytest.mark.usefixtures("agent_flask_apps")
def test_deletion_basic(agent_map: Dict[str, AgentResponse], owner_manager: AgentManager) -> None:
    basic_agents = [agent for agent in agent_map.values() if is_owned_by_agent(agent)]
    for basic_agent in basic_agents:
        owner_manager.delete_agent(basic_agent.system.id)

    for basic_agent in basic_agents:
        del agent_map[basic_agent.system.id]


@pytest.mark.order(-1)
@pytest.mark.usefixtures("agent_flask_apps")
def test_deletion_owner(agent_map: Dict[str, AgentResponse], user_manager: AgentManager) -> None:
    for agent in agent_map.values():  # should be the only one in the map
        user_manager.delete_agent(agent.system.id)
