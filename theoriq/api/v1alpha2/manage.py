import json
from typing import Dict, List, Optional, Sequence

from ...types import AgentDataObject
from ..common import AuthRepresentative
from . import AgentResponse


class AgentManager(AuthRepresentative):
    def get_agents(self) -> List[AgentResponse]:
        return self._client.get_agents()

    def get_agent(self, agent_id: str) -> AgentResponse:
        return self._client.get_agent(agent_id=agent_id)

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
