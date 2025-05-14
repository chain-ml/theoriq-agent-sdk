from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Optional

from biscuit_auth import KeyPair
from pydantic import BaseModel

from . import AgentResponse, ProtocolClient
from .protocol.biscuit_provider import BiscuitProvider, BiscuitProviderFactory
from ...biscuit import TheoriqRequest


class Metadata(BaseModel):
    name: str
    shortDescription: str
    longDescription: str
    tags: List[str]
    examplePrompts: List[str]
    costCard: Optional[str] = None
    imageUrl: Optional[str] = None


class Header(BaseModel):
    name: str
    value: str


class DeploymentConfiguration(BaseModel):
    headers: List[Header]
    url: str


class VirtualConfiguration(BaseModel):
    agentId: str
    configuration: Dict[str, Any]


class Configuration(BaseModel):
    deployment: Optional[DeploymentConfiguration] = None
    virtual: Optional[VirtualConfiguration] = None


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

    def create_agent(self, metadata: Metadata, configuration: Configuration) -> AgentResponse:
        payload_dict = {"metadata": metadata.model_dump(), "configuration": configuration.model_dump(exclude_none=True)}
        payload = json.dumps(payload_dict).encode("utf-8")
        biscuit = self._biscuit_provider.get_biscuit()
        return self._client.post_agent(biscuit=biscuit, content=payload)

    def configure_agent(self, agent_id: str, metadata: Metadata, config: Dict[str, Any]):
        configuration = Configuration(virtual=VirtualConfiguration(agentId=agent_id, configuration=config))
        agent = self.create_agent(metadata=metadata, configuration=configuration)

        theoriq_request = TheoriqRequest.from_body(
            body=agent.configuration.virtual.configuration_hash.encode("utf-8"),
            from_addr="USER_ADDRESS",  # user address
            to_addr=agent.system.id,
        )
        theoriq_biscuit = self._biscuit_provider.get_biscuit()
        theoriq_biscuit = theoriq_biscuit.attenuate(theoriq_request.to_theoriq_fact(uuid.uuid4()))

        return self._client.post_configure(biscuit=theoriq_biscuit, to_addr=agent.system.id)

    def update_agent(
        self, agent_id: str, metadata: Optional[Metadata] = None, configuration: Optional[Configuration] = None
    ) -> AgentResponse:
        payload_dict: Dict[str, Any] = {}
        if metadata is not None:
            payload_dict["metadata"] = metadata.model_dump()
        if configuration is not None:
            payload_dict["configuration"] = configuration.model_dump(exclude_none=True)

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
