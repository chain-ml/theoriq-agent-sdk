"""
Shared pytest fixtures for integration tests to manage Flask applications and agent state.
"""

import logging
import threading
from typing import Dict, Generator, List

import pytest
from tests.integration.utils import (
    TEST_AGENT_DATA_LIST,
    TEST_PARENT_AGENT_DATA,
    join_threads,
    run_echo_agents,
    run_agent,
)
from pydantic import BaseModel, Field

from theoriq.api.v1alpha2 import AgentResponse

# Global state for all integration tests
global_agent_maps: Dict[str, Dict[str, AgentResponse]] = {
    "test_as_agent": {
        "parent": {},
        "children": {}
    },
    "test_as_user": {},
    "test_configurable": {},
    "test_pub_sub": {},
}


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
    echo_threads = []  # run_echo_agents(TEST_AGENT_DATA_LIST)
    
    # Start configurable agent for test_configurable.py
    configurable_thread = run_agent(
        agent_data_obj=TEST_PARENT_AGENT_DATA, 
        schema=TestConfig.model_json_schema()
    )
    
    all_threads = echo_threads + [configurable_thread]
    
    yield all_threads
    
    # Cleanup: join all threads
    join_threads(all_threads)


@pytest.fixture(scope="session", autouse=True)
def setup_and_cleanup_agent_state():
    """
    Session-scoped fixture that ensures clean state at the beginning and end of test session.
    This runs automatically for all tests.
    """
    # Clear all global state at the beginning
    for test_name, state in global_agent_maps.items():
        if isinstance(state, dict):
            if "parent" in state and "children" in state:
                # For test_as_agent structure
                state["parent"].clear()
                state["children"].clear()
            else:
                # For other test structures
                state.clear()
    
    yield
    
    # Clear state after all tests complete
    for test_name, state in global_agent_maps.items():
        if isinstance(state, dict):
            if "parent" in state and "children" in state:
                state["parent"].clear()
                state["children"].clear()
            else:
                state.clear()


def get_agent_map(test_name: str, sub_map: str = None) -> Dict[str, AgentResponse]:
    """
    Helper function to get the appropriate agent map for a test.
    
    Args:
        test_name: Name of the test file (e.g., "test_as_user")
        sub_map: For test_as_agent, specify "parent" or "children"
    
    Returns:
        Dictionary mapping agent IDs to AgentResponse objects
    """
    if test_name == "test_as_agent" and sub_map:
        return global_agent_maps[test_name][sub_map]
    return global_agent_maps[test_name] 