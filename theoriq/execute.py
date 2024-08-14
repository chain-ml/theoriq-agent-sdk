"""
execute.py

Types and functions used by an Agent when executing a theoriq request
"""

from __future__ import annotations

from typing import Callable, Sequence

from .agent import Agent
from .biscuit import RequestBiscuit, ResponseBiscuit, TheoriqBudget, TheoriqCost
from .protocol.protocol_client import ProtocolClient
from .schemas import DialogItem, ExecuteRequestBody, ItemBlock
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

    @property
    def request_id(self) -> str:
        return str(self._request_biscuit.request_facts.req_id)

    @property
    def budget(self) -> TheoriqBudget:
        return self._request_biscuit.request_facts.budget


class ExecuteRequest:
    """
    This class encapsulates the necessary details retrieved from a request to the `execute` endpoint.

    Attributes:
        body (ExecuteRequestBody): Encapsulates the payload sent to the 'execute' endpoint.
        biscuit (RequestBiscuit): Holds the authentication information sent to the 'execute' endpoint.
    """

    def __init__(self, body: ExecuteRequestBody, request_biscuit: RequestBiscuit) -> None:
        self.body = body
        self._biscuit = request_biscuit

    @property
    def dialog_items(self) -> Sequence[DialogItem]:
        """
        Returns the dialog items contained in the request.
        """
        return self.body.dialog.items


class ExecuteResponse:
    """
    Represents the result of executing a theoriq request.

    Attributes:
        body (DialogItem): The body to encapsulate in the response payload.
        theoriq_cost (TheoriqCost): Cost of the processing of the request.
        status_code (int, optional): The status code of the response.
    """

    def __init__(
        self, body: DialogItem, cost: TheoriqCost = TheoriqCost.zero(Currency.USDC), status_code: int = 200
    ) -> None:
        self.body = body
        self.theoriq_cost = cost
        self.status_code = status_code

    @classmethod
    def cost_free(cls, source: str, blocks: Sequence[ItemBlock]) -> ExecuteResponse:
        """Creates a new `ExecuteResponse` with default values"""
        return ExecuteResponse(body=DialogItem.new(source=source, blocks=blocks))


ExecuteRequestFn = Callable[[ExecuteContext, ExecuteRequestBody], ExecuteResponse]
