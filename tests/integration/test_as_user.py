import logging
import os
import time
from typing import Dict, Final

import dotenv
import pytest
from tests.integration.utils import TEST_AGENT_DATA_LIST, get_echo_execute_output, nap, run_echo_agents

from theoriq.api.v1alpha2 import AgentResponse
from theoriq.api.v1alpha2.manage import AgentManager
from theoriq.api.v1alpha2.message import Messenger
from theoriq.biscuit import TheoriqBudget
from theoriq.dialog import TextItemBlock

dotenv.load_dotenv()

THEORIQ_API_KEY: Final[str] = os.environ["THEORIQ_API_KEY"]
user_manager = AgentManager.from_api_key(api_key=THEORIQ_API_KEY)

global_agent_map: Dict[str, AgentResponse] = {}


@pytest.fixture(scope="session", autouse=True)
def flask_apps():
    logging.basicConfig(level=logging.INFO)
    threads = run_echo_agents(TEST_AGENT_DATA_LIST)
    yield

    for thread in threads:
        thread.join(timeout=2.0)


@pytest.mark.order(1)
def test_registration():
    for agent_data_obj in TEST_AGENT_DATA_LIST:
        agent = user_manager.create_agent(agent_data_obj)
        print(f"Successfully registered `{agent.metadata.name}` with id=`{agent.system.id}`\n")
        global_agent_map[agent.system.id] = agent
        nap()


@pytest.mark.order(2)
def test_minting():
    for agent_id in global_agent_map.keys():
        user_manager.mint_agent(agent_id)
        print(f"Successfully minted `{agent_id}`\n")
        nap()


@pytest.mark.order(3)
def test_get_agents():
    agents = user_manager.get_agents()
    assert len(agents) > 0
    nap()

    for agent in agents:
        assert agent.system.id in global_agent_map
        assert agent == global_agent_map[agent.system.id]

        same_agent = user_manager.get_agent(agent.system.id)
        assert same_agent == agent
        nap()


@pytest.mark.order(4)
def test_unminting():
    for agent_id in global_agent_map.keys():
        user_manager.unmint_agent(agent_id)
        print(f"Successfully unminted `{agent_id}`\n")
        nap()


@pytest.mark.order(5)
def test_messenger():
    message = "Hello"
    blocks = [TextItemBlock(message)]
    messenger = Messenger.from_api_key(api_key=THEORIQ_API_KEY, user_address=os.environ["USER_ADDRESS"])

    for agent_id, agent in global_agent_map.items():
        response = messenger.send_request(blocks=blocks, budget=TheoriqBudget.empty(), to_addr=agent_id)
        assert response.body.extract_last_text() == get_echo_execute_output(
            message=message, agent_name=agent.metadata.name
        )


@pytest.mark.order(-1)
def test_deletion():
    for agent in global_agent_map.values():
        user_manager.delete_agent(agent.system.id)
        print(f"Successfully deleted `{agent.system.id}`\n")
        time.sleep(0.5)
