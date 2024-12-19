from typing import Any, Callable
from uuid import UUID

from theoriq import Agent
from theoriq.api.v1alpha2 import ProtocolClient
from theoriq.biscuit import AgentAddress, TheoriqBiscuit, RequestBiscuit


class ConfigureContext:
    def __init__(self, agent: Agent, protocol_client: ProtocolClient) -> None:
        self._agent = agent
        self._protocol_client = protocol_client

    def set_virtual_address(self, address: str) -> None:
        self._agent.virtual_address = AgentAddress(address)

    @property
    def virtual_address(self) -> AgentAddress:
        return self._agent.virtual_address


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
        self, configure_context: ConfigureContext, payload: Any, biscuit: TheoriqBiscuit, body: bytes, request_id: UUID
    ):
        client = configure_context._protocol_client
        biscuit = RequestBiscuit(biscuit.biscuit)
        try:
            self.configure_fn(configure_context, payload)
            client.post_request_success(biscuit, body, request_id)
        except:
            client.post_request_failure(biscuit, body, request_id)

    @classmethod
    def default(cls) -> "AgentConfigurator":
        """
        Creates a default instance of AgentConfigurator.
        Useful when the agent does not require any configuration.
        """

        def default_configure_fn(context, config):
            return None

        def default_is_long_running_fn(context, config):
            return False

        return cls(default_configure_fn, default_is_long_running_fn)
