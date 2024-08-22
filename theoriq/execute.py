"""
execute.py

Types and functions used by an Agent when executing a theoriq request
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Sequence

from .agent import Agent
from .biscuit import RequestBiscuit, ResponseBiscuit, TheoriqBudget, TheoriqCost
from .biscuit.facts import TheoriqRequest
from .protocol.protocol_client import ProtocolClient
from .schemas import DialogItem, ExecuteRequestBody, ItemBlock
from .schemas.request import Dialog
from .types import Currency


class ExecuteContext:
    """ """

    def __init__(self, agent: Agent, protocol_client: ProtocolClient, request_biscuit: RequestBiscuit) -> None:
        self._protocol_client = protocol_client
        self._agent = agent
        self._request_biscuit = request_biscuit

    def send_event(self, message: str) -> None:
        self._protocol_client.post_event(request_biscuit=self._request_biscuit, message=message)

    def new_response_biscuit(self, body: bytes, cost: TheoriqCost) -> ResponseBiscuit:
        """Build a biscuit for the response to an 'execute' request."""
        return self._agent.attenuate_biscuit_for_response(self._request_biscuit, body, cost)

    def new_error_response_biscuit(self, body: bytes) -> ResponseBiscuit:
        """Build a biscuit for the response to an 'execute' request."""
        return self._agent.attenuate_biscuit_for_response(self._request_biscuit, body, TheoriqCost.zero(Currency.USDC))

    def new_free_response(self, blocks=Sequence[ItemBlock]) -> ExecuteResponse:
        return self.new_response(blocks=blocks, cost=TheoriqCost.zero(Currency.USDC))

    def new_response(self, blocks: Sequence[ItemBlock], cost: TheoriqCost) -> ExecuteResponse:
        return ExecuteResponse(dialog_item=DialogItem.new(source=self.agent_address, blocks=blocks), cost=cost)

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

    @property
    def agent_address(self) -> str:
        return str(self._agent.config.address)

    @property
    def request_id(self) -> str:
        return str(self._request_biscuit.request_facts.req_id)

    @property
    def budget(self) -> TheoriqBudget:
        return self._request_biscuit.request_facts.budget


class ExecuteResponse:
    """
    Represents the result of executing a theoriq request.

    Attributes:
        body (DialogItem): The body to encapsulate in the response payload.
        theoriq_cost (TheoriqCost): Cost of the processing of the request.
        status_code (int, optional): The status code of the response.
    """

    def __init__(
        self, dialog_item: DialogItem, cost: TheoriqCost = TheoriqCost.zero(Currency.USDC), status_code: int = 200
    ) -> None:
        self.body = dialog_item
        self.theoriq_cost = cost
        self.status_code = status_code

    def __str__(self):
        return f"ExecuteResponse(body={self.body}, cost={self.theoriq_cost}, status_code={self.status_code})"

    @classmethod
    def from_protocol_response(cls, data: Dict[str, Any], status_code: int) -> ExecuteResponse:
        dialog_item = DialogItem.from_dict(data["dialog_item"])
        return cls(
            dialog_item=dialog_item,
            cost=TheoriqCost.zero(Currency.USDC),
            status_code=status_code,
        )


ExecuteRequestFn = Callable[[ExecuteContext, ExecuteRequestBody], ExecuteResponse]
