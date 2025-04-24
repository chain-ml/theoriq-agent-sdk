import logging
import threading
import time
from typing import List, Sequence

from flask import Flask

from theoriq import AgentDeploymentConfiguration, ExecuteContext, ExecuteResponse
from theoriq.api.v1alpha2 import ExecuteRequestFn
from theoriq.api.v1alpha2.schemas import ExecuteRequestBody
from theoriq.dialog import TextItemBlock
from theoriq.extra.flask.v1alpha2.flask import theoriq_blueprint
from theoriq.types import AgentDataObject

logger = logging.getLogger(__name__)


def get_echo_execute(agent_name: str) -> ExecuteRequestFn:
    def execute(context: ExecuteContext, req: ExecuteRequestBody) -> ExecuteResponse:
        last_item = req.last_item
        if last_item is None:
            raise RuntimeError("Got empty dialog")
        text_value = last_item.blocks[-1].data.text

        logger.info(f"Got request for {agent_name}: {text_value}")

        return context.new_free_response(blocks=[TextItemBlock(text=f"{text_value} from {agent_name}!")])

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
    port = int(agent_data_obj.spec.urls.end_point.split(":")[-1])

    thread = threading.Thread(target=run_agent_flask_app, args=(execute, agent_config, port))
    thread.daemon = True
    thread.start()
    return thread


def run_echo_agents(agent_data_objs: Sequence[AgentDataObject], sleep_time: float = 2.0) -> List[threading.Thread]:
    """Run a list of agents in separate threads."""

    threads: List[threading.Thread] = []
    for agent_data_obj in agent_data_objs:
        threads.append(run_echo_agent(agent_data_obj))
        time.sleep(sleep_time)

    return threads
