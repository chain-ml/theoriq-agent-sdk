"""
execute.py

Types and functions used by an Agent when executing a Theoriq request
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence

from theoriq.agent import Agent
from theoriq.biscuit import AgentAddress, RequestBiscuit, ResponseBiscuit, TheoriqBiscuit, TheoriqBudget
from theoriq.biscuit.facts import TheoriqRequest
from theoriq.dialog import Dialog, DialogItem, ItemBlock
from theoriq.types import AgentMetadata, Metric

from ...types.agent_data import AgentDescriptions
from .protocol.protocol_client import ProtocolClient, RequestStatus
from .request_context_base import ExecuteResponse, RequestContextBase
from .schemas.request import Configuration, ExecuteRequestBody


class ExecuteContext(RequestContextBase):
    """
    Represents the context for executing a request, managing interactions with the agent and protocol client.
    """

    def __init__(
        self,
        agent: Agent,
        protocol_client: ProtocolClient,
        request_biscuit: RequestBiscuit,
        request_body: ExecuteRequestBody,
    ) -> None:
        """
        Initializes an ExecuteContext instance.

        Args:
            agent (Agent): The agent responsible for handling the execution.
            protocol_client (ProtocolClient): The client responsible for communicating with the protocol.
            request_biscuit (RequestBiscuit): The biscuit associated with the request, containing metadata and permissions.
        """

        configuration = request_body.configuration
        virtual_address = AgentAddress(configuration.fromRef.id) if configuration else None
        super().__init__(agent, protocol_client, request_biscuit, virtual_address)
        self._configuration_hash = configuration.fromRef.hash if configuration else None
        self._request_body = request_body

    def send_event(self, message: str) -> None:
        """
        Sends an event message via the protocol client.

        Args:
            message (str): The message to send as an event.
        """
        self._protocol_client.post_event(request_biscuit=self._request_biscuit, message=message)

    def send_metrics(self, metrics: List[Metric]):
        """
        Sends agent metrics via the protocol client.

        Args:
            metrics (List[MetricRequest]): The list of metrics to send.
        """
        self._protocol_client.post_metrics(request_biscuit=self._request_biscuit, metrics=metrics)

    def send_metric(self, metric: Metric):
        """
        Sends agent metrics via the protocol client.

        Args:
            metric (MetricRequest): The metric to send.
        """
        self._protocol_client.post_metrics(request_biscuit=self._request_biscuit, metrics=[metric])

    def send_notification(self, notification: bytes):
        """
        Sends agent notification via the protocol client.
        """
        biscuit = TheoriqBiscuit(self._request_biscuit.biscuit)
        self._protocol_client.post_notification(
            biscuit=biscuit, agent_id=str(self.agent_address), notification=notification
        )

    def send_request(self, blocks: Sequence[ItemBlock], budget: TheoriqBudget, to_addr: str) -> ExecuteResponse:
        """
        Sends a request to another address, attenuating the biscuit for the request and handling the response.

        Args:
            blocks (Sequence[ItemBlock]): The blocks of data to include in the request.
            budget (TheoriqBudget): The budget for processing the request.
            to_addr (str): The address to which the request is sent.

        Returns:
            ExecuteResponse: The response received from the request.
        """
        config = self._agent.config
        execute_request_body = ExecuteRequestBody(
            dialog=Dialog(items=[DialogItem.new(source=str(self.agent_address), blocks=blocks)])
        )
        body = execute_request_body.model_dump_json().encode("utf-8")
        theoriq_request = TheoriqRequest.from_body(body=body, from_addr=config.address, to_addr=to_addr)
        request_biscuit = self._request_biscuit.attenuate_for_request(theoriq_request, budget, config.private_key)
        response = self._protocol_client.post_request(request_biscuit=request_biscuit, content=body, to_addr=to_addr)
        return ExecuteResponse.from_protocol_response({"dialog_item": response}, 200)

    def complete_request(self, response_biscuit: ResponseBiscuit, body: bytes):
        biscuit = TheoriqBiscuit(response_biscuit.biscuit)
        request_id = response_biscuit.resp_facts.req_id
        self._protocol_client.post_request_complete(
            request_id=request_id, biscuit=biscuit, body=body, status=RequestStatus.SUCCESS
        )

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

    def _sender_metadata(self, agent_id: str) -> AgentMetadata:
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


ExecuteRequestFn = Callable[[ExecuteContext, ExecuteRequestBody], ExecuteResponse]
"""
Type alias for a function that takes an ExecuteContext and an ExecuteRequestBody,
and returns an ExecuteResponse.
"""
