"""
Shared pytest fixtures for integration tests to manage Flask applications and agent state.
"""

import logging
import threading
from typing import Generator, List

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
    dotenv.load_dotenv()
    logging.basicConfig(level=logging.INFO)

    # Start all echo agents
    echo_threads = run_echo_agents(TEST_AGENT_DATA_LIST)

    # Start configurable agent for test_configurable.py
    configurable_thread = run_agent(agent_data_obj=TEST_PARENT_AGENT_DATA, schema=TestConfig.model_json_schema())

    all_threads = echo_threads + [configurable_thread]

    yield all_threads

    # Cleanup: join all threads
    join_threads(all_threads)
