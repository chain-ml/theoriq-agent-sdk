import logging
import os
from typing import Dict, Final, Generator

import dotenv
import pytest
from tests.integration.utils import (
    PARENT_AGENT_ENV_PREFIX,
    PARENT_AGENT_NAME,
    TEST_AGENT_DATA_LIST,
    TEST_CHILD_AGENT_DATA_LIST,
    TEST_PARENT_AGENT_DATA,
    get_echo_execute_output,
    join_threads,
    run_echo_agents,
)
from tests.integration.conftest import get_agent_map

from theoriq.api.v1alpha2 import AgentResponse
from theoriq.api.v1alpha2.manage import DeployedAgentManager
from theoriq.api.v1alpha2.message import Messenger
from theoriq.biscuit import TheoriqBudget
from theoriq.dialog import TextItemBlock

dotenv.load_dotenv()
THEORIQ_API_KEY: Final[str] = os.environ["THEORIQ_API_KEY"]
user_manager = DeployedAgentManager.from_api_key(api_key=THEORIQ_API_KEY)


# Use shared fixtures instead of local ones
@pytest.mark.usefixtures("shared_flask_apps")
@pytest.mark.order(1)
def test_registration_parent() -> None:
    global_parent_agent_map = get_agent_map("test_as_agent", "parent")
    agent = user_manager.create_agent(
        metadata=TEST_PARENT_AGENT_DATA.spec.metadata, configuration=TEST_PARENT_AGENT_DATA.spec.configuration
    )
    print(f"Successfully registered `{agent.metadata.name}` with id=`{agent.system.id}`\n")
    global_parent_agent_map[agent.system.id] = agent


@pytest.mark.usefixtures("shared_flask_apps")
@pytest.mark.order(2)
def test_registration_children() -> None:
    global_children_agent_map = get_agent_map("test_as_agent", "children")
    manager = DeployedAgentManager.from_env(env_prefix=PARENT_AGENT_ENV_PREFIX)
    for child_agent_data_obj in TEST_CHILD_AGENT_DATA_LIST:
        agent = manager.create_agent(
            metadata=child_agent_data_obj.spec.metadata, configuration=child_agent_data_obj.spec.configuration
        )
        print(f"Successfully registered `{agent.metadata.name}` with id=`{agent.system.id}`\n")
        global_children_agent_map[agent.system.id] = agent


# test mint, get, unmint here when minting functionality is implemented


@pytest.mark.usefixtures("shared_flask_apps")
@pytest.mark.order(3)
def test_messenger() -> None:
    global_parent_agent_map = get_agent_map("test_as_agent", "parent")
    global_children_agent_map = get_agent_map("test_as_agent", "children")
    all_agents: Dict[str, AgentResponse] = {**global_parent_agent_map, **global_children_agent_map}

    # messaging from children to parent doesn't work because there's no minting
    # so testing parent-to-all instead of all-to-all

    messenger = Messenger.from_env(env_prefix=PARENT_AGENT_ENV_PREFIX)
    for receiver_id, receiver in all_agents.items():
        message = f"Hello from {PARENT_AGENT_NAME}"
        blocks = [TextItemBlock(message)]
        response = messenger.send_request(blocks=blocks, budget=TheoriqBudget.empty(), to_addr=receiver_id)
        assert response.body.extract_last_text() == get_echo_execute_output(
            message=message, agent_name=receiver.metadata.name
        )


@pytest.mark.usefixtures("shared_flask_apps")
@pytest.mark.order(-2)
def test_deletion_children() -> None:
    global_children_agent_map = get_agent_map("test_as_agent", "children")
    manager = DeployedAgentManager.from_env(env_prefix=PARENT_AGENT_ENV_PREFIX)

    for child_agent in global_children_agent_map.values():
        manager.delete_agent(child_agent.system.id)
        print(f"Successfully deleted `{child_agent.system.id}`\n")


@pytest.mark.usefixtures("shared_flask_apps")
@pytest.mark.order(-1)
def test_deletion_parent() -> None:
    global_parent_agent_map = get_agent_map("test_as_agent", "parent")
    for agent in global_parent_agent_map.values():
        user_manager.delete_agent(agent.system.id)
        print(f"Successfully deleted `{agent.system.id}`\n")
