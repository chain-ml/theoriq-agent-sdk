import logging
import os
from copy import deepcopy
from typing import Dict, Final, Generator

import dotenv
import pytest
from biscuit_auth import KeyPair
from tests.integration.utils import (
    PARENT_AGENT_ENV_PREFIX,
    TEST_AGENT_DATA_LIST,
    TEST_PARENT_AGENT_DATA,
    get_echo_execute_output,
    nap,
    run_echo_agents,
)

from theoriq import AgentDeploymentConfiguration
from theoriq.api.v1alpha2 import AgentResponse
from theoriq.api.v1alpha2.manage import AgentManager
from theoriq.api.v1alpha2.message import Messenger
from theoriq.biscuit import AgentAddress, TheoriqBudget
from theoriq.dialog import TextItemBlock

dotenv.load_dotenv()

THEORIQ_API_KEY: Final[str] = os.environ["THEORIQ_API_KEY"]
user_manager = AgentManager.from_api_key(api_key=THEORIQ_API_KEY)

global_agent_map: Dict[str, AgentResponse] = {}


@pytest.fixture(scope="session", autouse=True)
def flask_apps() -> Generator[None, None, None]:
    logging.basicConfig(level=logging.INFO)
    threads = run_echo_agents(TEST_AGENT_DATA_LIST)
    yield

    for thread in threads:
        thread.join(timeout=2.0)


@pytest.mark.order(1)
def test_registration() -> None:
    for agent_data_obj in TEST_AGENT_DATA_LIST:
        agent = user_manager.create_agent(agent_data_obj)
        print(f"Successfully registered `{agent.metadata.name}` with id=`{agent.system.id}`\n")
        global_agent_map[agent.system.id] = agent
        nap()


@pytest.mark.order(2)
def test_minting() -> None:
    for agent_id in global_agent_map.keys():
        user_manager.mint_agent(agent_id)
        print(f"Successfully minted `{agent_id}`\n")
        nap()


@pytest.mark.order(3)
def test_get_agents() -> None:
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
def test_unminting() -> None:
    for agent_id in global_agent_map.keys():
        user_manager.unmint_agent(agent_id)
        print(f"Successfully unminted `{agent_id}`\n")
        nap()


@pytest.mark.order(5)
def test_messenger() -> None:
    message = "Hello"
    blocks = [TextItemBlock(message)]
    messenger = Messenger.from_api_key(api_key=THEORIQ_API_KEY)

    for agent_id, agent in global_agent_map.items():
        response = messenger.send_request(blocks=blocks, budget=TheoriqBudget.empty(), to_addr=agent_id)
        assert response.body.extract_last_text() == get_echo_execute_output(
            message=message, agent_name=agent.metadata.name
        )


@pytest.mark.order(6)
def test_updating() -> None:
    agent_data_obj = deepcopy(TEST_PARENT_AGENT_DATA)
    agent_data_obj.metadata.name = "Updated Parent Agent"

    config = AgentDeploymentConfiguration.from_env(env_prefix=PARENT_AGENT_ENV_PREFIX)
    key_pair = KeyPair.from_private_key(config.private_key)
    address = AgentAddress.from_public_key(key_pair.public_key)
    response = user_manager.update_agent(agent_data_obj, agent_id=str(address))

    assert response.metadata.name == "Updated Parent Agent"


@pytest.mark.order(-1)
def test_deletion() -> None:
    for agent in global_agent_map.values():
        user_manager.delete_agent(agent.system.id)
        print(f"Successfully deleted `{agent.system.id}`\n")
        nap()
