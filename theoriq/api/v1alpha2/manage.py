from __future__ import annotations

import json
from typing import Dict, List, Optional, Sequence

from ...types import AgentDataObject
from . import AgentResponse, ProtocolClient
from .protocol.biscuit_provider import BiscuitProvider, BiscuitProviderFactory


class AgentManager:
    def __init__(self, biscuit_provider: BiscuitProvider, client: Optional[ProtocolClient] = None) -> None:
        self._client = client or ProtocolClient.from_env()
        self._biscuit_provider = biscuit_provider

    def get_agents(self) -> List[AgentResponse]:
        biscuit = self._biscuit_provider.get_biscuit()
        return self._client.get_agents(biscuit)

    def get_agent(self, agent_id: str) -> AgentResponse:
        biscuit = self._biscuit_provider.get_biscuit()
        return self._client.get_agent(agent_id=agent_id, biscuit=biscuit)

    def create_agent(
        self, agent_data_obj: AgentDataObject, headers: Optional[Sequence[Dict[str, str]]] = None
    ) -> AgentResponse:
        payload = json.dumps(agent_data_obj.to_payload(headers)).encode("utf-8")
        biscuit = self._biscuit_provider.get_biscuit()
        return self._client.post_agent(biscuit=biscuit, content=payload)

    def update_agent(
        self, agent_data_obj: AgentDataObject, agent_id: str, headers: Optional[Sequence[Dict[str, str]]] = None
    ) -> AgentResponse:
        payload = json.dumps(agent_data_obj.to_payload(headers)).encode("utf-8")
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
