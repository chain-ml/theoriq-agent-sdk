import glob
import logging
import os
import time
from typing import Dict, List

import dotenv
import pytest
from tests import DATA_DIR
from tests.integration.dev_utils.run_agents_utils import run_echo_agents

from theoriq.api.v1alpha2 import AgentResponse, ProtocolClient
from theoriq.api.v1alpha2.manage import AgentManager
from theoriq.api.v1alpha2.message import Messenger
from theoriq.biscuit import TheoriqBudget
from theoriq.dialog import TextItemBlock
from theoriq.types import AgentDataObject

dotenv.load_dotenv()

agent_data_objs: List[AgentDataObject] = [AgentDataObject.from_yaml(path) for path in glob.glob(DATA_DIR + "/*.yaml")]
global_agent_map: Dict[str, AgentResponse] = {}
manager = AgentManager.from_api_key(api_key=os.environ["API_KEY"])


def nap():
    time.sleep(0.25)


@pytest.fixture(scope="session", autouse=True)
def flask_apps():
    logging.basicConfig(level=logging.INFO)
    threads = run_echo_agents(agent_data_objs)
    yield

    for thread in threads:
        thread.join(timeout=2.0)


@pytest.mark.order(1)
def test_registration():
    for agent_data_obj in agent_data_objs:
        agent = manager.create_agent(agent_data_obj)
        print(f"Successfully registered `{agent.metadata.name}` with id=`{agent.system.id}`\n")
        nap()

        global_agent_map[agent.system.id] = agent


@pytest.mark.order(2)
def test_minting():
    for agent_id in global_agent_map.keys():
        manager.mint_agent(agent_id)
        print(f"Successfully minted `{agent_id}`\n")
        nap()


@pytest.mark.order(3)
def test_get_agents():
    client = ProtocolClient.from_env()
    agents = client.get_agents()
    assert len(agents) > 0
    nap()

    for agent in agents:
        assert agent.system.id in global_agent_map
        assert agent == global_agent_map[agent.system.id]

        same_agent = client.get_agent(agent.system.id)
        assert same_agent == agent
        nap()


@pytest.mark.order(4)
def test_unminting():
    for agent_id in global_agent_map.keys():
        manager.unmint_agent(agent_id)
        print(f"Successfully unminted `{agent_id}`\n")
        nap()


@pytest.mark.order(5)
def test_messenger_as_agents():
    messenger = Messenger.from_env(env_prefix="A_")
    response = messenger.send_request(
        blocks=[TextItemBlock("Hello")],
        budget=TheoriqBudget.empty(),
        to_addr="0x5766206e8ca2ca78267d0682e7d3edf2560c2b4076aea8ad2a77b69b3976483b",
    )
    expected = response.body.blocks[0].to_str()
    assert expected == "Hello from Agent B!"


@pytest.mark.order(6)
def test_messenger_as_user():
    pass


@pytest.mark.order(-1)
def test_deletion():
    for agent in global_agent_map.values():
        manager.delete_agent(agent.system.id)
        print(f"Successfully deleted `{agent.system.id}`\n")
        time.sleep(0.5)
