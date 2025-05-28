import os
import threading
from typing import Dict, Generator, List

import dotenv
import pytest
from tests import DATA_DIR
from tests.integration.agent_registry import AgentRegistry
from tests.integration.agent_runner import AgentRunner, TestConfig

from theoriq.api.v1alpha2 import AgentResponse
from theoriq.api.v1alpha2.manage import DeployedAgentManager
from theoriq.api.v1alpha2.message import Messenger

dotenv.load_dotenv()


@pytest.fixture(scope="session")
def agent_registry() -> AgentRegistry:
    return AgentRegistry.from_dir(DATA_DIR)


@pytest.fixture(scope="session")
def agent_flask_apps(agent_registry: AgentRegistry) -> Generator[List[threading.Thread], None, None]:
    """Shared fixture that runs all agent Flask applications needed for integration tests."""

    agent_runner = AgentRunner()
    for agent in agent_registry.get_child_agents():
        agent_runner.run_non_configurable_agent(agent)
    for agent in agent_registry.get_parent_agents():
        agent_runner.run_non_configurable_agent(agent)
    for agent in agent_registry.get_configurable_agents():
        agent_runner.run_configurable_agent(agent, TestConfig.model_json_schema())

    yield agent_runner.running_threads

    agent_runner.stop_all()


@pytest.fixture(scope="module")
def agent_map() -> Generator[Dict[str, AgentResponse], None, None]:
    """File-level fixture that returns a mutable dictionary for storing registered agents."""
    agent_map: Dict[str, AgentResponse] = {}
    yield agent_map
    agent_map.clear()


@pytest.fixture()
def user_manager() -> DeployedAgentManager:
    return DeployedAgentManager.from_api_key(api_key=os.environ["THEORIQ_API_KEY"])


@pytest.fixture()
def user_messenger() -> Messenger:
    return Messenger.from_api_key(api_key=os.environ["THEORIQ_API_KEY"])
