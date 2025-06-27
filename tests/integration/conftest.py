import os
from typing import Dict, Final, Generator

import dotenv
import pytest
from tests import DATA_DIR
from tests.integration.agent_registry import AgentRegistry, AgentType
from tests.integration.agent_runner import AgentRunner, TestConfig

from theoriq.api.v1alpha2 import AgentResponse
from theoriq.api.v1alpha2.manage import AgentManager
from theoriq.api.v1alpha2.message import Messenger

dotenv.load_dotenv()

STRING_SCHEMA: Final[Dict[str, str]] = {"type": "string"}


@pytest.fixture(scope="session")
def agent_registry() -> AgentRegistry:
    return AgentRegistry.from_dir(DATA_DIR)


@pytest.fixture(scope="session")
def agent_flask_apps(agent_registry: AgentRegistry) -> Generator[None, None, None]:
    """Shared fixture that runs all agent Flask applications needed for integration tests."""

    agent_runner = AgentRunner()

    non_configurable_agents = agent_registry.get_agents_of_types([AgentType.OWNER, AgentType.BASIC])
    for agent in non_configurable_agents:
        agent_runner.run_non_configurable_agent(
            agent, request_schema=STRING_SCHEMA, response_schema=STRING_SCHEMA, notification_schema=STRING_SCHEMA
        )

    configurable_agents = agent_registry.get_agents_of_type(AgentType.CONFIGURABLE)
    for agent in configurable_agents:
        agent_runner.run_configurable_agent(agent, configuration_schema=TestConfig.model_json_schema())

    yield

    agent_runner.stop_all()


@pytest.fixture(scope="module")
def agent_map() -> Generator[Dict[str, AgentResponse], None, None]:
    """File-level fixture that returns a mutable dictionary for storing registered agents."""
    agent_map: Dict[str, AgentResponse] = {}
    yield agent_map
    agent_map.clear()


@pytest.fixture()
def user_manager() -> AgentManager:
    return AgentManager.from_api_key(api_key=os.environ["THEORIQ_API_KEY"])


@pytest.fixture()
def user_messenger() -> Messenger:
    return Messenger.from_api_key(api_key=os.environ["THEORIQ_API_KEY"])


@pytest.fixture()
def owner_manager(agent_registry: AgentRegistry) -> DeployedAgentManager:
    owner_agent_data = agent_registry.get_first_agent_of_type(AgentType.OWNER)
    return DeployedAgentManager.from_env(env_prefix=owner_agent_data.metadata.labels["env_prefix"])


@pytest.fixture()
def owner_messenger(agent_registry: AgentRegistry) -> Messenger:
    owner_agent_data = agent_registry.get_first_agent_of_type(AgentType.OWNER)
    return Messenger.from_env(env_prefix=owner_agent_data.metadata.labels["env_prefix"])
