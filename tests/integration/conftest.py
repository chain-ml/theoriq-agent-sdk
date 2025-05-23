"""
Shared pytest fixtures for integration tests to manage Flask applications and agent state.
"""

import logging
import os
import threading
from typing import Dict, Generator, List

import dotenv
import pytest
from pydantic import BaseModel, Field
from tests.integration.utils import (
    TEST_AGENT_DATA_LIST,
    TEST_PARENT_AGENT_DATA,
    join_threads,
    run_agent,
    run_echo_agents,
)

from theoriq.api.v1alpha2 import AgentResponse
from theoriq.api.v1alpha2.manage import DeployedAgentManager
from theoriq.api.v1alpha2.message import Messenger

dotenv.load_dotenv()


class TestConfig(BaseModel):
    """Test configuration schema used by configurable tests."""

    text: str = Field(description="Text field")
    number: int = Field(description="An integer number")


@pytest.fixture(scope="session")
def shared_flask_apps() -> Generator[List[threading.Thread], None, None]:
    """
    Shared fixture that runs all Flask applications needed for integration tests.
    This runs all echo agents plus the configurable agent.
    """
    logging.basicConfig(level=logging.INFO)

    # Start all echo agents
    echo_threads = run_echo_agents(TEST_AGENT_DATA_LIST)

    # Start configurable agent for test_configurable.py
    configurable_thread = run_agent(agent_data_obj=TEST_PARENT_AGENT_DATA, schema=TestConfig.model_json_schema())

    all_threads = echo_threads + [configurable_thread]

    yield all_threads

    # Cleanup: join all threads
    join_threads(all_threads)


@pytest.fixture(scope="session")
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
