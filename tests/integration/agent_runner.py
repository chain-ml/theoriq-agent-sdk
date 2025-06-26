import json
import logging
import threading
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from theoriq import AgentDeploymentConfiguration, ExecuteContext, ExecuteResponse
from theoriq.api.v1alpha2 import ExecuteRequestFn
from theoriq.api.v1alpha2.schemas import AgentSchemas, ExecuteRequestBody, ExecuteSchema
from theoriq.extra.flask import run_agent_flask_app
from theoriq.extra.flask.v1alpha2.flask import theoriq_blueprint
from theoriq.types import AgentDataObject

logger = logging.getLogger(__name__)


class TestConfig(BaseModel):
    text: str = Field(description="Text field")
    number: int = Field(description="An integer number")


class AgentRunner:
    """Manages Flask applications for test agents."""

    def __init__(self) -> None:
        self._running_threads: List[threading.Thread] = []

    @staticmethod
    def get_echo_execute_output(*, message: str, agent_name: str) -> str:
        return f"Got `{message}` as {agent_name}!"

    @staticmethod
    def get_configurable_execute_output(config: Dict[str, Any], *, message: str, agent_name: str) -> str:
        config_str = json.dumps(dict(sorted(config.items())))
        return f"Got `{message}` as {agent_name}! Configured with `{config_str}`"

    @classmethod
    def create_echo_execute_fn(cls, agent_name: str) -> ExecuteRequestFn:
        def execute(context: ExecuteContext, req: ExecuteRequestBody) -> ExecuteResponse:
            message = req.last_text
            response = cls.get_echo_execute_output(message=message, agent_name=agent_name)
            logger.info(response)
            return context.new_text_response(text=response)

        return execute

    @classmethod
    def create_configurable_execute_fn(cls, agent_name: str) -> ExecuteRequestFn:
        def execute_configurable(context: ExecuteContext, req: ExecuteRequestBody) -> ExecuteResponse:
            config: Optional[Dict[str, Any]] = context.agent_configuration
            if config is None:
                raise ValueError(f"{agent_name} - Empty configuration")

            message = req.last_text
            response = cls.get_configurable_execute_output(config=config, message=message, agent_name=agent_name)
            logger.info(response)
            return context.new_text_response(text=response)

        return execute_configurable

    def run_agent(self, agent_data: AgentDataObject, schemas: AgentSchemas) -> threading.Thread:
        """
        Start agent Flask app in a separate daemon thread with the assumption
        that `env_prefix` is contained in labels of AgentDataObject.

        If schemas.configuration is provided, use echo_execute_configurable(), otherwise echo_execute().
        """
        agent_config = AgentDeploymentConfiguration.from_env(env_prefix=agent_data.metadata.labels["env_prefix"])
        deployment = agent_data.spec.configuration.ensure_deployment

        try:
            port = int(deployment.url.split(":")[-1])
        except (ValueError, AttributeError, IndexError):
            logger.error("Invalid deployment URL format: %s", deployment.url)
            raise

        agent_name = agent_data.spec.metadata.name
        execute = (
            self.create_echo_execute_fn(agent_name)
            if schemas.configuration is None
            else self.create_configurable_execute_fn(agent_name)
        )

        blueprint = theoriq_blueprint(agent_config=agent_config, execute_fn=execute, schemas=schemas)

        thread = threading.Thread(target=run_agent_flask_app, args=(blueprint, port, "0.0.0.0", None, logging.INFO))
        thread.daemon = True
        thread.start()

        self._running_threads.append(thread)
        return thread

    def run_non_configurable_agent(
        self,
        agent_data: AgentDataObject,
        *,
        request_schema: Dict[str, Any],
        response_schema: Dict[str, Any],
        notification_schema: Dict[str, Any],
    ) -> threading.Thread:
        # non-configurable agent act as publisher in test_pub_sub.py
        schemas = AgentSchemas(
            execute={"sample": ExecuteSchema(request=request_schema, response=response_schema)},
            notification=notification_schema,
        )
        return self.run_agent(agent_data, schemas=schemas)

    def run_configurable_agent(
        self, agent_data: AgentDataObject, configuration_schema: Dict[str, Any]
    ) -> threading.Thread:
        return self.run_agent(agent_data, schemas=AgentSchemas(configuration=configuration_schema))

    def stop_all(self, timeout: float = 0.5) -> None:
        for thread in self._running_threads:
            thread.join(timeout=timeout)
        self._running_threads.clear()
