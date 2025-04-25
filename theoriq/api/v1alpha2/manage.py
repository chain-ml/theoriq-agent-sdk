from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from biscuit_auth import PrivateKey

from theoriq import AgentDeploymentConfiguration
from theoriq.biscuit import AgentAddress

from ...types import AgentDataObject
from . import AgentResponse
from .protocol.biscuit_provider import BiscuitProvider, BiscuitProviderFromAPIKey, BiscuitProviderFromPrivateKey
from .protocol.protocol_client import ProtocolClient


class AgentManager:
    def __init__(self, biscuit_provider: BiscuitProvider, client: Optional[ProtocolClient] = None) -> None:
        self._client = client or ProtocolClient.from_env()
        self._biscuit_provider = biscuit_provider

    def get_agents(self) -> List[AgentResponse]:
        return self._client.get_agents()

    def get_agent(self, agent_id: str) -> AgentResponse:
        return self._client.get_agent(agent_id=agent_id)

    @staticmethod
    def _agent_data_obj_to_payload(agent_data_obj: AgentDataObject) -> Dict[str, Any]:
        # TODO: clarify/fix AgentDataObject schema; provide to_payload()
        return {
            "configuration": {
                "deployment": {
                    "headers": [{"name": "name", "value": "value"}],
                    "url": agent_data_obj.spec.urls.end_point,
                },
            },
            "metadata": {
                "name": agent_data_obj.spec.metadata.name,
                "shortDescription": agent_data_obj.spec.metadata.descriptions.short,
                "longDescription": agent_data_obj.spec.metadata.descriptions.long,
                "tags": agent_data_obj.spec.metadata.tags,
                "examplePrompts": agent_data_obj.spec.metadata.examples,
                "imageUrl": agent_data_obj.spec.urls.icon,
                "costCard": agent_data_obj.spec.metadata.cost_card,
            },
        }

    def create_agent(self, agent_data_obj: AgentDataObject) -> AgentResponse:
        payload = json.dumps(self._agent_data_obj_to_payload(agent_data_obj)).encode("utf-8")

        biscuit = self._biscuit_provider.get_biscuit()
        return self._client.post_agent(biscuit=biscuit, content=payload)

    def update_agent(self, agent_data_obj: AgentDataObject, agent_id: str) -> AgentResponse:
        payload = json.dumps(self._agent_data_obj_to_payload(agent_data_obj)).encode("utf-8")

        biscuit = self._biscuit_provider.get_biscuit()
        return self._client.patch_agent(biscuit=biscuit, content=payload, agent_id=agent_id)

    def mint_agent(self, agent_id: str) -> AgentResponse:
        return self._client.post_mint(biscuit=self._biscuit_provider.get_biscuit(), agent_id=agent_id)

    def unmint_agent(self, agent_id: str) -> AgentResponse:
        return self._client.post_unmint(biscuit=self._biscuit_provider.get_biscuit(), agent_id=agent_id)

    def delete_agent(self, agent_id: str) -> None:
        self._client.delete_agent(biscuit=self._biscuit_provider.get_biscuit(), agent_id=agent_id)

    @classmethod
    def from_api_key(cls, api_key: str, client: Optional[ProtocolClient] = None) -> AgentManager:
        protocol_client = client or ProtocolClient.from_env()
        biscuit_provider = BiscuitProviderFromAPIKey(api_key=api_key, client=protocol_client)
        return cls(biscuit_provider=biscuit_provider, client=protocol_client)

    @classmethod
    def from_agent(
        cls, private_key: PrivateKey, address: Optional[AgentAddress] = None, client: Optional[ProtocolClient] = None
    ) -> AgentManager:
        protocol_client = client or ProtocolClient.from_env()
        biscuit_provider = BiscuitProviderFromPrivateKey(
            private_key=private_key, address=address, client=protocol_client
        )
        return cls(biscuit_provider=biscuit_provider, client=protocol_client)

    @classmethod
    def from_env(cls, env_prefix: str = "") -> AgentManager:
        config = AgentDeploymentConfiguration.from_env(env_prefix=env_prefix)
        return cls.from_agent(private_key=config.private_key)
