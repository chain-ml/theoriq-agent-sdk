from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Optional

from typing_extensions import Self

from ...biscuit import TheoriqRequest
from ...types import AgentConfiguration, AgentDataObject, AgentMetadata
from . import AgentResponse, ProtocolClient
from .protocol.biscuit_provider import BiscuitProvider, BiscuitProviderFactory


class AgentConfigurationError(Exception):
    def __init__(self, message: str, agent: AgentResponse, original_exception: Exception) -> None:
        self.message = message
        self.agent = agent
        self.original_exception = original_exception

    def __str__(self) -> str:
        return self.message


class AgentManager:
    """Provides capabilities to manage Theoriq agents."""

    def __init__(self, biscuit_provider: BiscuitProvider, client: Optional[ProtocolClient] = None) -> None:
        self._client = client or ProtocolClient.from_env()
        self._biscuit_provider = biscuit_provider

    def get_agents(self) -> List[AgentResponse]:
        biscuit = self._biscuit_provider.get_biscuit()
        return self._client.get_agents(biscuit)

    def get_agent(self, agent_id: str) -> AgentResponse:
        biscuit = self._biscuit_provider.get_biscuit()
        return self._client.get_agent(agent_id=agent_id, biscuit=biscuit)

    def create_agent(self, metadata: AgentMetadata, configuration: AgentConfiguration) -> AgentResponse:
        agent = self._create_agent(metadata=metadata, configuration=configuration)

        if configuration.deployment is not None:
            return agent  # deployed agent
        # virtual agent
        return self._try_configure_agent(agent, f"Agent {agent.system.id} created but failed to configure")

    def create_agent_from_data(self, agent_data: AgentDataObject) -> AgentResponse:
        return self.create_agent(agent_data.spec.metadata, agent_data.spec.configuration)

    def _create_agent(self, metadata: AgentMetadata, configuration: AgentConfiguration) -> AgentResponse:
        payload_dict = {"metadata": metadata.to_dict(), "configuration": configuration.to_dict()}
        payload = json.dumps(payload_dict).encode("utf-8")
        biscuit = self._biscuit_provider.get_biscuit()
        return self._client.post_agent(biscuit=biscuit, content=payload)

    def _configure_agent(self, *, agent_id: str, configuration_hash: str) -> AgentResponse:
        theoriq_request = TheoriqRequest.from_body(
            body=configuration_hash.encode("utf-8"),
            from_addr=self._biscuit_provider.address,
            to_addr=agent_id,
        )
        theoriq_biscuit = self._biscuit_provider.get_request_biscuit(request_id=uuid.uuid4(), facts=[theoriq_request])
        return self._client.post_configure(biscuit=theoriq_biscuit, to_addr=agent_id)

    def _try_configure_agent(self, agent: AgentResponse, error_message: str) -> AgentResponse:
        try:
            return self._configure_agent(
                agent_id=agent.system.id, configuration_hash=agent.configuration.ensure_virtual.configuration_hash
            )
        except Exception as e:
            raise AgentConfigurationError(message=error_message, agent=agent, original_exception=e) from e

    def update_agent(
        self,
        agent_id: str,
        metadata: Optional[AgentMetadata] = None,
        configuration: Optional[AgentConfiguration] = None,
    ) -> AgentResponse:
        agent = self._update_agent(agent_id=agent_id, metadata=metadata, configuration=configuration)

        if configuration is None or configuration.deployment is not None:
            return agent  # deployed agent
        # virtual agent
        return self._try_configure_agent(agent, f"Agent {agent.system.id} updated but failed to configure")

    def update_agent_from_data(self, agent_id: str, agent_data: AgentDataObject) -> AgentResponse:
        return self.update_agent(
            agent_id, metadata=agent_data.spec.metadata, configuration=agent_data.spec.maybe_configuration
        )

    def _update_agent(
        self,
        agent_id: str,
        metadata: Optional[AgentMetadata] = None,
        configuration: Optional[AgentConfiguration] = None,
    ) -> AgentResponse:
        payload_dict: Dict[str, Any] = {}
        if metadata is not None:
            payload_dict["metadata"] = metadata.to_dict()
        if configuration is not None:
            payload_dict["configuration"] = configuration.to_dict()

        payload = json.dumps(payload_dict).encode("utf-8")
        biscuit = self._biscuit_provider.get_biscuit()
        return self._client.patch_agent(biscuit=biscuit, content=payload, agent_id=agent_id)

    def mint_agent(self, agent_id: str) -> AgentResponse:
        return self._client.post_mint(biscuit=self._biscuit_provider.get_biscuit(), agent_id=agent_id)

    def unmint_agent(self, agent_id: str) -> AgentResponse:
        return self._client.post_unmint(biscuit=self._biscuit_provider.get_biscuit(), agent_id=agent_id)

    def delete_agent(self, agent_id: str) -> None:
        self._client.delete_agent(biscuit=self._biscuit_provider.get_biscuit(), agent_id=agent_id)

    @classmethod
    def from_api_key(cls, api_key: str) -> Self:
        return cls(biscuit_provider=BiscuitProviderFactory.from_api_key(api_key=api_key))

    @classmethod
    def from_env(cls, env_prefix: str = "") -> Self:
        return cls(biscuit_provider=BiscuitProviderFactory.from_env(env_prefix=env_prefix))
