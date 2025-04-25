import logging
import os
from typing import Dict, Final

import dotenv
import pytest
from tests.integration.utils import (
    PARENT_AGENT_ENV_PREFIX,
    TEST_AGENT_DATA_LIST,
    TEST_CHILD_AGENT_DATA_LIST,
    TEST_PARENT_AGENT_DATA,
    nap,
    run_echo_agents,
)

from theoriq.api.v1alpha2 import AgentResponse
from theoriq.api.v1alpha2.manage import AgentManager
from theoriq.api.v1alpha2.message import Messenger
from theoriq.biscuit import TheoriqBudget
from theoriq.dialog import TextItemBlock

dotenv.load_dotenv()
THEORIQ_API_KEY: Final[str] = os.environ["THEORIQ_API_KEY"]
user_manager = AgentManager.from_api_key(api_key=THEORIQ_API_KEY)

global_parent_agent_map: Dict[str, AgentResponse] = {}
global_children_agent_map: Dict[str, AgentResponse] = {}


@pytest.fixture(scope="session", autouse=True)
def flask_apps():
    logging.basicConfig(level=logging.INFO)
    threads = run_echo_agents(TEST_AGENT_DATA_LIST)
    yield

    for thread in threads:
        thread.join(timeout=2.0)


@pytest.mark.order(1)
def test_registration_parent():
    agent = user_manager.create_agent(TEST_PARENT_AGENT_DATA)
    print(f"Successfully registered `{agent.metadata.name}` with id=`{agent.system.id}`\n")
    global_parent_agent_map[agent.system.id] = agent
    nap()


@pytest.mark.order(2)
def test_registration_children():
    manager = AgentManager.from_env(env_prefix=PARENT_AGENT_ENV_PREFIX)
    for child_agent_data_obj in TEST_CHILD_AGENT_DATA_LIST:
        agent = manager.create_agent(child_agent_data_obj)
        print(f"Successfully registered `{agent.metadata.name}` with id=`{agent.system.id}`\n")
        global_children_agent_map[agent.system.id] = agent
        nap()


# TODO: test mint, get, unmint here when minting functionality is implemented


@pytest.mark.order(3)
def test_messenger():
    messenger = Messenger.from_env(env_prefix="A_")
    response = messenger.send_request(
        blocks=[TextItemBlock("Hello")],
        budget=TheoriqBudget.empty(),
        to_addr="0x5766206e8ca2ca78267d0682e7d3edf2560c2b4076aea8ad2a77b69b3976483b",
    )
    expected = response.body.blocks[0].to_str()
    assert expected == "Hello from Agent B!"


@pytest.mark.order(-2)
def test_deletion_children():
    manager = AgentManager.from_env(env_prefix=PARENT_AGENT_ENV_PREFIX)

    for child_agent in global_children_agent_map.values():
        manager.delete_agent(child_agent.system.id)
        print(f"Successfully deleted `{child_agent.system.id}`\n")
        nap()


@pytest.mark.order(-1)
def test_deletion_parent():
    for agent in global_parent_agent_map.values():
        user_manager.delete_agent(agent.system.id)
        print(f"Successfully deleted `{agent.system.id}`\n")
        nap()
