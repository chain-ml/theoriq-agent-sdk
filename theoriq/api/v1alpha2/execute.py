"""
execute.py

Types and functions used by an Agent when executing a Theoriq request
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence

from theoriq.agent import Agent
from theoriq.biscuit import AgentAddress, RequestBiscuit, TheoriqBudget
from theoriq.biscuit.facts import TheoriqRequest
from theoriq.dialog import Dialog, DialogItem, ItemBlock
from theoriq.types import Metric

from ..common import ExecuteContextBase, ExecuteResponse
from .protocol.protocol_client import ProtocolClient
from .schemas.request import Configuration, ExecuteRequestBody


class ExecuteContext(ExecuteContextBase):
    """
    Represents the context for executing a request, managing interactions with the agent and protocol client.
    """

    def __init__(self, agent: Agent, protocol_client: ProtocolClient, request_biscuit: RequestBiscuit) -> None:
        """
        Initializes an ExecuteContext instance.

        Args:
            agent (Agent): The agent responsible for handling the execution.
            protocol_client (ProtocolClient): The client responsible for communicating with the protocol.
            request_biscuit (RequestBiscuit): The biscuit associated with the request, containing metadata and permissions.
        """
        super().__init__(agent, request_biscuit)
        self._protocol_client = protocol_client
        self._configuration_hash: Optional[str] = None

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


ExecuteRequestFn = Callable[[ExecuteContext, ExecuteRequestBody], ExecuteResponse]
"""
Type alias for a function that takes an ExecuteContext and an ExecuteRequestBody,
and returns an ExecuteResponse.
"""
