from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Optional

from ...biscuit import TheoriqRequest
from ...types import AgentConfiguration, AgentMetadata, VirtualConfiguration
from . import AgentResponse, ProtocolClient
from .protocol.biscuit_provider import BiscuitProvider, BiscuitProviderFactory


class AgentManager:
    """Provides capabilities to create, update, mint, unmint and manage agents."""

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
        payload_dict = {"metadata": metadata.to_dict(), "configuration": configuration.to_dict()}
        payload = json.dumps(payload_dict).encode("utf-8")
        biscuit = self._biscuit_provider.get_biscuit()
        return self._client.post_agent(biscuit=biscuit, content=payload)

    def configure_agent(self, agent_id: str, metadata: AgentMetadata, config: Dict[str, Any]) -> AgentResponse:
        configuration = AgentConfiguration(virtual=VirtualConfiguration(agent_id=agent_id, configuration=config))
        agent = self.create_agent(metadata=metadata, configuration=configuration)

        if agent.configuration.virtual is None:
            raise RuntimeError

        theoriq_request = TheoriqRequest.from_body(
            body=agent.configuration.virtual.configuration_hash.encode("utf-8"),
            from_addr="USER_ADDRESS",  # user address
            to_addr=agent.system.id,
        )
        theoriq_biscuit = self._biscuit_provider.get_biscuit()
        theoriq_biscuit = theoriq_biscuit.attenuate(theoriq_request.to_theoriq_fact(uuid.uuid4()))

        return self._client.post_configure(biscuit=theoriq_biscuit, to_addr=agent.system.id)

    def update_agent(
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
    def from_api_key(cls, api_key: str) -> AgentManager:
        return AgentManager(biscuit_provider=BiscuitProviderFactory.from_api_key(api_key=api_key))

    @classmethod
    def from_env(cls, env_prefix: str = "") -> AgentManager:
        return AgentManager(biscuit_provider=BiscuitProviderFactory.from_env(env_prefix=env_prefix))
