import os
from typing import Dict, Generator

import pytest
from tests.integration.utils import (
    PARENT_AGENT_ENV_PREFIX,
    PARENT_AGENT_NAME,
    TEST_CHILD_AGENT_DATA_LIST,
    TEST_PARENT_AGENT_DATA,
    get_echo_execute_output,
)

from theoriq.api.v1alpha2 import AgentResponse
from theoriq.api.v1alpha2.manage import DeployedAgentManager
from theoriq.api.v1alpha2.message import Messenger
from theoriq.biscuit import TheoriqBudget
from theoriq.dialog import TextItemBlock


@pytest.fixture(scope="session")
def parent_agent_map() -> Generator[Dict[str, AgentResponse], None, None]:
    """File-level fixture that returns a mutable dictionary for storing parent agents."""
    agent_map: Dict[str, AgentResponse] = {}
    yield agent_map
    agent_map.clear()


@pytest.fixture(scope="session")
def children_agent_map() -> Generator[Dict[str, AgentResponse], None, None]:
    """File-level fixture that returns a mutable dictionary for storing child agents."""
    agent_map: Dict[str, AgentResponse] = {}
    yield agent_map
    agent_map.clear()


@pytest.fixture()
def user_manager() -> DeployedAgentManager:
    """Manager for user operations (parent agents)."""
    return DeployedAgentManager.from_api_key(api_key=os.environ["THEORIQ_API_KEY"])


@pytest.fixture()
def parent_manager() -> DeployedAgentManager:
    """Manager for parent agent operations (child agents)."""
    return DeployedAgentManager.from_env(env_prefix=PARENT_AGENT_ENV_PREFIX)


@pytest.fixture()
def parent_messenger() -> Messenger:
    """Messenger for parent agent operations."""
    return Messenger.from_env(env_prefix=PARENT_AGENT_ENV_PREFIX)


@pytest.mark.order(1)
@pytest.mark.usefixtures("agent_flask_apps")
def test_registration_parent(parent_agent_map: Dict[str, AgentResponse], user_manager: DeployedAgentManager) -> None:
    agent = user_manager.create_agent(
        metadata=TEST_PARENT_AGENT_DATA.spec.metadata, configuration=TEST_PARENT_AGENT_DATA.spec.configuration
    )
    print(f"Successfully registered `{agent.metadata.name}` with id=`{agent.system.id}`\n")
    parent_agent_map[agent.system.id] = agent


@pytest.mark.order(2)
@pytest.mark.usefixtures("agent_flask_apps")
def test_registration_children(
    children_agent_map: Dict[str, AgentResponse], parent_manager: DeployedAgentManager
) -> None:
    for child_agent_data_obj in TEST_CHILD_AGENT_DATA_LIST:
        agent = parent_manager.create_agent(
            metadata=child_agent_data_obj.spec.metadata, configuration=child_agent_data_obj.spec.configuration
        )
        print(f"Successfully registered `{agent.metadata.name}` with id=`{agent.system.id}`\n")
        children_agent_map[agent.system.id] = agent


# test mint, get, unmint here when minting functionality is implemented


@pytest.mark.order(3)
@pytest.mark.usefixtures("agent_flask_apps")
def test_messenger(
    parent_agent_map: Dict[str, AgentResponse],
    children_agent_map: Dict[str, AgentResponse],
    parent_messenger: Messenger,
) -> None:
    all_agents: Dict[str, AgentResponse] = {**parent_agent_map, **children_agent_map}

    # messaging from children to parent doesn't work because there's no minting
    # so testing parent-to-all instead of all-to-all

    for receiver_id, receiver in all_agents.items():
        message = f"Hello from {PARENT_AGENT_NAME}"
        blocks = [TextItemBlock(message)]
        response = parent_messenger.send_request(blocks=blocks, budget=TheoriqBudget.empty(), to_addr=receiver_id)
        assert response.body.extract_last_text() == get_echo_execute_output(
            message=message, agent_name=receiver.metadata.name
        )


@pytest.mark.order(-2)
@pytest.mark.usefixtures("agent_flask_apps")
def test_deletion_children(children_agent_map: Dict[str, AgentResponse], parent_manager: DeployedAgentManager) -> None:
    for child_agent in children_agent_map.values():
        parent_manager.delete_agent(child_agent.system.id)
        print(f"Successfully deleted `{child_agent.system.id}`\n")


@pytest.mark.order(-1)
@pytest.mark.usefixtures("agent_flask_apps")
def test_deletion_parent(parent_agent_map: Dict[str, AgentResponse], user_manager: DeployedAgentManager) -> None:
    for agent in parent_agent_map.values():
        user_manager.delete_agent(agent.system.id)
        print(f"Successfully deleted `{agent.system.id}`\n")
