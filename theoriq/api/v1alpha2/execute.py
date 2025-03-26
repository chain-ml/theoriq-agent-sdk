"""
execute.py

Types and functions used by an Agent when executing a Theoriq request
"""

from __future__ import annotations

from typing import Callable, Sequence

from theoriq.agent import Agent
from theoriq.biscuit import RequestBiscuit, ResponseBiscuit, TheoriqBiscuit, TheoriqBudget
from theoriq.biscuit.facts import TheoriqRequest
from theoriq.dialog import Dialog, DialogItem, ItemBlock
from theoriq.types import AgentMetadata

from ..common import ExecuteContextBase, ExecuteResponse
from .base_context import BaseContext
from .protocol.protocol_client import ProtocolClient, RequestStatus
from .schemas.request import ExecuteRequestBody


class ExecuteContext(ExecuteContextBase, BaseContext):
    """
    Represents the context for executing a request, managing interactions with the agent and protocol client.
    """

    def __init__(self, agent: Agent, protocol_client: ProtocolClient, request_biscuit: RequestBiscuit) -> None:
        BaseContext.__init__(self, agent, protocol_client, request_biscuit)
        ExecuteContextBase.__init__(self, agent, request_biscuit)

    def complete_request(self, response_biscuit: ResponseBiscuit, body: bytes):
        biscuit = TheoriqBiscuit(response_biscuit.biscuit)
        request_id = response_biscuit.resp_facts.req_id
        self._protocol_client.post_request_complete(
            request_id=request_id, biscuit=biscuit, body=body, status=RequestStatus.SUCCESS
        )

    def _sender_metadata(self, agent_id: str) -> AgentMetadata:
        return self._get_agent_metadata(agent_id)

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


ExecuteRequestFn = Callable[[ExecuteContext, ExecuteRequestBody], ExecuteResponse]
"""
Type alias for a function that takes an ExecuteContext and an ExecuteRequestBody,
and returns an ExecuteResponse.
"""
