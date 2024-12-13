from typing import Any, Callable

from theoriq import Agent
from theoriq.api.v1alpha2 import ProtocolClient
from theoriq.biscuit import AgentAddress


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
