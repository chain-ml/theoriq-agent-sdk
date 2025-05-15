"""
Utility functions to run agents Flask apps and manage test data objects.
"""

import glob
import logging
import threading
import time
from typing import Final, List, Sequence

from flask import Flask
from tests import DATA_DIR

from theoriq import AgentDeploymentConfiguration, ExecuteContext, ExecuteResponse
from theoriq.api.v1alpha2 import AgentResponse, ExecuteRequestFn
from theoriq.api.v1alpha2.schemas import ExecuteRequestBody
from theoriq.extra.flask.v1alpha2.flask import theoriq_blueprint
from theoriq.types import AgentDataObject

logger = logging.getLogger(__name__)

TEST_AGENT_DATA_LIST: Final[List[AgentDataObject]] = [
    AgentDataObject.from_yaml(path) for path in glob.glob(DATA_DIR + "/*.yaml")
]

PARENT_AGENT_NAME: Final[str] = "Parent Agent"
PARENT_AGENT_ENV_PREFIX: Final[str] = "PARENT_"

maybe_parent_agent_data = next(
    (agent for agent in TEST_AGENT_DATA_LIST if agent.spec.metadata.name == PARENT_AGENT_NAME),
    None,
)
if maybe_parent_agent_data is None:
    raise RuntimeError("Parent agent data object not found")
TEST_PARENT_AGENT_DATA: Final[AgentDataObject] = maybe_parent_agent_data

TEST_CHILD_AGENT_DATA_LIST: Final[List[AgentDataObject]] = [
    agent for agent in TEST_AGENT_DATA_LIST if agent.metadata.name != PARENT_AGENT_NAME
]


def get_echo_execute_output(*, message: str, agent_name: str) -> str:
    return f"Got `{message}` as {agent_name}!"


def get_echo_execute(agent_name: str) -> ExecuteRequestFn:
    def execute(context: ExecuteContext, req: ExecuteRequestBody) -> ExecuteResponse:
        message = req.last_text
        logger.info(f"Got request for {agent_name}: {message}")
        return context.new_free_text_response(text=get_echo_execute_output(message=message, agent_name=agent_name))

    return execute


def run_agent_flask_app(execute: ExecuteRequestFn, agent_config: AgentDeploymentConfiguration, port: int) -> None:
    app = Flask(f"{agent_config.prefix} on port {port}")

    blueprint = theoriq_blueprint(agent_config, execute)
    app.register_blueprint(blueprint)
    app.run(host="0.0.0.0", port=port)


def run_echo_agent(agent_data_obj: AgentDataObject) -> threading.Thread:
    """Run an agent in a separate daemon thread with the assumption that env_prefix is contained in labels."""
    agent_name = agent_data_obj.spec.metadata.name
    execute = get_echo_execute(agent_name)
    agent_config = AgentDeploymentConfiguration.from_env(env_prefix=agent_data_obj.metadata.labels["env_prefix"])
    configuration = agent_data_obj.spec.configuration
    if configuration is None or configuration.deployment is None:
        raise RuntimeError("No deployment information")
    port = int(configuration.deployment.url.split(":")[-1])

    thread = threading.Thread(target=run_agent_flask_app, args=(execute, agent_config, port))
    thread.daemon = True
    thread.start()
    return thread


def run_echo_agents(agent_data_objs: Sequence[AgentDataObject], sleep_time: float = 0.5) -> List[threading.Thread]:
    """Run a list of agents in separate threads."""

    threads: List[threading.Thread] = []
    for agent_data_obj in agent_data_objs:
        threads.append(run_echo_agent(agent_data_obj))
        time.sleep(sleep_time)

    return threads


def join_threads(threads: Sequence[threading.Thread], timeout: float = 0.5) -> None:
    """Shout down a list of agent threads."""

    for thread in threads:
        thread.join(timeout=timeout)


def agents_are_equal(a: AgentResponse, b: AgentResponse) -> bool:
    return (
        a.system.id == b.system.id
        and a.system.public_key == b.system.public_key
        and a.system.owner_address == b.system.owner_address
        # and a.system.state == b.system.state  # state is different before and after minting
        and a.system.metadata_hash == b.system.metadata_hash
        and a.system.configuration_hash == b.system.configuration_hash
        and a.system.tags == b.system.tags
        and a.metadata.name == b.metadata.name
        and a.metadata.short_description == b.metadata.short_description
        and a.metadata.long_description == b.metadata.long_description
        and a.metadata.tags == b.metadata.tags
        and a.metadata.cost_card == b.metadata.cost_card
        and a.metadata.example_prompts == b.metadata.example_prompts
    )
