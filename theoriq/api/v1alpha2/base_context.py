"""
base_context.py

Base context class containing common functionality for Execute and Subscribe contexts
"""

from typing import Any, Dict, List, Optional, Sequence

from theoriq.agent import Agent
from theoriq.biscuit import AgentAddress, RequestBiscuit, TheoriqBiscuit, TheoriqBudget
from theoriq.biscuit.facts import TheoriqRequest
from theoriq.dialog import Dialog, DialogItem, ItemBlock
from theoriq.types import AgentMetadata, Metric

from ...types.agent_data import AgentDescriptions
from ..common import ExecuteResponse
from .protocol.protocol_client import ProtocolClient
from .schemas.request import Configuration, ExecuteRequestBody


class BaseContext:
    def __init__(self, agent: Agent, protocol_client: ProtocolClient, request_biscuit: RequestBiscuit) -> None:
        self._agent: Agent = agent
        self._protocol_client: ProtocolClient = protocol_client
        self._request_biscuit: RequestBiscuit = request_biscuit
        self._configuration_hash: Optional[str] = None

    def send_event(self, message: str) -> None:
        self._protocol_client.post_event(request_biscuit=self._request_biscuit, message=message)

    def send_metrics(self, metrics: List[Metric]):
        self._protocol_client.post_metrics(request_biscuit=self._request_biscuit, metrics=metrics)

    def send_metric(self, metric: Metric):
        self._protocol_client.post_metrics(request_biscuit=self._request_biscuit, metrics=[metric])

    def send_notification(self, notification: bytes):
        biscuit = self.agent_biscuit()
        self._protocol_client.post_notification(biscuit=biscuit, agent_id=self.agent_address, notification=notification)

    def send_request(self, blocks: Sequence[ItemBlock], budget: TheoriqBudget, to_addr: str) -> ExecuteResponse:
        config = self._agent.config
        execute_request_body = ExecuteRequestBody(
            dialog=Dialog(items=[DialogItem.new(source=self.agent_address, blocks=blocks)])
        )
        body = execute_request_body.model_dump_json().encode("utf-8")
        theoriq_request = TheoriqRequest.from_body(body=body, from_addr=config.address, to_addr=to_addr)
        request_biscuit = self._request_biscuit.attenuate_for_request(theoriq_request, budget, config.private_key)
        response = self._protocol_client.post_request(request_biscuit=request_biscuit, content=body, to_addr=to_addr)
        return ExecuteResponse.from_protocol_response({"dialog_item": response}, 200)

    def set_configuration(self, configuration: Optional[Configuration]) -> None:
        if not configuration:
            return

        self._agent.virtual_address = AgentAddress(configuration.fromRef.id)
        self._configuration_hash = configuration.fromRef.hash

    @property
    def agent_configuration(self) -> Optional[Dict[str, Any]]:
        virtual_address = self._agent.virtual_address
        if virtual_address.is_null or not self._configuration_hash:
            return None
        try:
            return self._protocol_client.get_configuration(
                request_biscuit=self._request_biscuit,
                agent_address=virtual_address,
                configuration_hash=self._configuration_hash,
            )
        except RuntimeError:
            return {}

    def agent_biscuit(self) -> TheoriqBiscuit:
        authentication_biscuit = self._agent.authentication_biscuit()
        agent_public_key = self._agent.config.public_key
        biscuit_response = self._protocol_client.get_biscuit(authentication_biscuit, agent_public_key)

        protocol_public_key = self._protocol_client.public_key
        return TheoriqBiscuit.from_token(token=biscuit_response.biscuit, public_key=protocol_public_key)

    def _get_agent_metadata(self, agent_id: str) -> AgentMetadata:
        agent_response = self._protocol_client.get_agent(agent_id=agent_id)
        metadata = agent_response.metadata
        descriptions = AgentDescriptions(short=metadata.short_description, long=metadata.long_description)
        return AgentMetadata(
            name=metadata.name,
            descriptions=descriptions,
            tags=metadata.tags,
            examples=metadata.example_prompts,
            cost_card=metadata.cost_card,
        )

    @property
    def agent_address(self) -> str:
        """
        Returns the address of the agent.
        If the agent is virtual return the virtual address

        Returns:
            str: The agent's address as a string.
        """
        if self._agent.virtual_address.is_null:
            return str(self._agent.config.address)
        return str(self._agent.virtual_address)
