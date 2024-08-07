"""
execute.py

Types and functions used by an Agent when executing a theoriq request
"""

from __future__ import annotations

from typing import Callable, Sequence

from .biscuit import RequestBiscuit, TheoriqBudget, TheoriqCost
from .schemas import DialogItem, ExecuteRequestBody, ItemBlock
from .types import Currency


class ExecuteRequest:
    """
    This class encapsulates the necessary details retrieved from a request to the `execute` endpoint.

    Attributes:
        body (ExecuteRequestBody): Encapsulates the payload sent to the 'execute' endpoint.
        biscuit (RequestBiscuit): Holds the authentication information sent to the 'execute' endpoint.
    """

    def __init__(self, body: ExecuteRequestBody, biscuit: RequestBiscuit) -> None:
        self.body = body
        self._biscuit = biscuit

    @property
    def dialog_items(self) -> Sequence[DialogItem]:
        """
        Returns the dialog items contained in the request.
        """
        return self.body.dialog.items

    @property
    def last_item(self) -> DialogItem:
        """
        Returns the last dialog item contained in the request based on timestamp.
        """

        return max(self.body.dialog.items, key=lambda obj: obj.timestamp)

    @property
    def request_id(self) -> str:
        return str(self._biscuit.request_facts.req_id)

    @property
    def budget(self) -> TheoriqBudget:
        return self._biscuit.request_facts.budget


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


ExecuteRequestFn = Callable[[ExecuteRequest], ExecuteResponse]
