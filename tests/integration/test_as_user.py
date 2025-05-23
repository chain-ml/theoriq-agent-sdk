import logging
import os
from copy import deepcopy
from typing import Dict, Final, Generator

import dotenv
import pytest
from tests.integration.utils import (
    PARENT_AGENT_ENV_PREFIX,
    TEST_AGENT_DATA_LIST,
    TEST_PARENT_AGENT_DATA,
    agents_are_equal,
    get_echo_execute_output,
    join_threads,
    run_echo_agents,
)

from theoriq import AgentDeploymentConfiguration
from theoriq.api.v1alpha2 import AgentResponse
from theoriq.api.v1alpha2.manage import DeployedAgentManager
from theoriq.api.v1alpha2.message import Messenger
from theoriq.biscuit import TheoriqBudget
from theoriq.dialog import TextItemBlock


@pytest.fixture(scope="session")
def agent_map() -> Generator[Dict[str, AgentResponse], None, None]:
    """File-level fixture that returns a mutable dictionary for storing registered agents."""
    agent_map = {}
    yield agent_map
    agent_map.clear()

@pytest.fixture()
def manager() -> DeployedAgentManager:
    return DeployedAgentManager.from_api_key(api_key=os.environ["THEORIQ_API_KEY"])

@pytest.fixture()
def messenger() -> Messenger:
    return Messenger.from_api_key(api_key=os.environ["THEORIQ_API_KEY"])


@pytest.mark.usefixtures("shared_flask_apps")
@pytest.mark.order(1)
def test_registration(agent_map: Dict[str, AgentResponse], manager: DeployedAgentManager) -> None:
    for agent_data_obj in TEST_AGENT_DATA_LIST:
        agent = manager.create_agent(
            metadata=agent_data_obj.spec.metadata, configuration=agent_data_obj.spec.configuration
        )
        print(f"Successfully registered `{agent.metadata.name}` with id=`{agent.system.id}`\n")
        agent_map[agent.system.id] = agent


@pytest.mark.usefixtures("shared_flask_apps")
@pytest.mark.order(2)
def test_minting(agent_map: Dict[str, AgentResponse], manager: DeployedAgentManager) -> None:
    for agent_id in agent_map.keys():
        agent = manager.mint_agent(agent_id)
        assert agent.system.state == "online"
        print(f"Successfully minted `{agent_id}`\n")


@pytest.mark.usefixtures("shared_flask_apps")
@pytest.mark.order(3)
def test_get_agents(agent_map: Dict[str, AgentResponse], manager: DeployedAgentManager) -> None:
    agents = manager.get_agents()
    assert len(agents) >= len(agent_map.keys())
    fetched_agents: Dict[str, AgentResponse] = {agent.system.id: agent for agent in agents}

    for agent in agent_map.values():
        assert agent.system.id in fetched_agents
        assert agents_are_equal(agent, fetched_agents[agent.system.id])

        same_agent = manager.get_agent(agent.system.id)
        assert agents_are_equal(agent, same_agent)


@pytest.mark.usefixtures("shared_flask_apps")
@pytest.mark.order(4)
def test_unminting(agent_map: Dict[str, AgentResponse], manager: DeployedAgentManager) -> None:
    for agent_id in agent_map.keys():
        agent = manager.unmint_agent(agent_id)
        assert agent.system.state == "configured"
        print(f"Successfully unminted `{agent_id}`\n")


@pytest.mark.usefixtures("shared_flask_apps")
@pytest.mark.order(5)
def test_messenger(agent_map: Dict[str, AgentResponse], messenger: Messenger) -> None:
    message = "Hello from user"
    blocks = [TextItemBlock(message)]

    for agent_id, agent in agent_map.items():
        response = messenger.send_request(blocks=blocks, budget=TheoriqBudget.empty(), to_addr=agent_id)
        assert response.body.extract_last_text() == get_echo_execute_output(
            message=message, agent_name=agent.metadata.name
        )


@pytest.mark.usefixtures("shared_flask_apps")
@pytest.mark.order(6)
def test_updating(manager: DeployedAgentManager) -> None:
    agent_data_obj = deepcopy(TEST_PARENT_AGENT_DATA)
    agent_data_obj.spec.metadata.name = "Updated Parent Agent"

    config = AgentDeploymentConfiguration.from_env(env_prefix=PARENT_AGENT_ENV_PREFIX)
    response = manager.update_agent(agent_id=str(config.address), metadata=agent_data_obj.spec.metadata)

    assert response.metadata.name == "Updated Parent Agent"


@pytest.mark.usefixtures("shared_flask_apps")
@pytest.mark.order(-1)
def test_deletion(agent_map: Dict[str, AgentResponse], manager: DeployedAgentManager) -> None:
    for agent in agent_map.values():
        manager.delete_agent(agent.system.id)
        print(f"Successfully deleted `{agent.system.id}`\n")
