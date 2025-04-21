from __future__ import annotations

import logging
from typing import Any, Callable

from theoriq import Agent
from theoriq.biscuit import AgentAddress, RequestFact, TheoriqBiscuit

from .protocol import ProtocolClient

logger = logging.getLogger(__name__)


class ConfigureContext:
    def __init__(self, agent: Agent, protocol_client: ProtocolClient) -> None:
        self._agent = agent
        self._protocol_client = protocol_client

    def set_virtual_address(self, address: str) -> None:
        self._agent.virtual_address = AgentAddress(address)

    @property
    def virtual_address(self) -> AgentAddress:
        return self._agent.virtual_address

    def post_request_success(self, biscuit: TheoriqBiscuit, message: str | None) -> None:
        self._protocol_client.post_request_success(biscuit, message, self._agent)

    def post_request_failure(self, biscuit: TheoriqBiscuit, message: str | None) -> None:
        self._protocol_client.post_request_failure(biscuit, message, self._agent)


ConfigureFn = Callable[[ConfigureContext, Any], None]
"""A callable type for the configuration function.

The function accepts:
- A `ConfigureContext` instance to provide the configuration context.
- Additional keyword arguments to build the configuration.
"""

IsLongRunningFn = Callable[[ConfigureContext, Any], bool]
"""A callable type for checking if a configuration is long-running.

:param
- A `ConfigureContext` instance to provide the configuration context.
- Additional keyword arguments to build the configuration.

:returns
- A boolean indicating whether the configuration is long-running.
"""


class AgentConfigurator:
    """
    A class to manage and execute configuration for agents.
    """

    def __init__(self, configure_fn: ConfigureFn, is_long_running_fn: IsLongRunningFn) -> None:
        self.configure_fn = configure_fn
        self.is_long_running_fn = is_long_running_fn

    def __call__(
        self, configure_context: ConfigureContext, payload: Any, biscuit: TheoriqBiscuit, agent: Agent
    ) -> None:
        try:
            self.configure_fn(configure_context, payload)
        except Exception as e:
            logger.error(f"Failed to configure agent: {e}")
            configure_context.post_request_failure(biscuit, str(e))
        else:
            request_fact = biscuit.read_fact(RequestFact)
            configured_agent_id = request_fact.from_addr
            message = f"Successfully configured agent {configured_agent_id}"
            logger.info(message)
            configure_context.post_request_success(biscuit, message)

    @classmethod
    def default(cls) -> AgentConfigurator:
        """
        Creates a default instance of AgentConfigurator.
        Useful when the agent does not require any configuration.
        """

        def default_configure_fn(_context: ConfigureContext, _config: Any) -> None:
            return None

        def default_is_long_running_fn(_context: ConfigureContext, _config: Any) -> bool:
            return False

        return cls(default_configure_fn, default_is_long_running_fn)
