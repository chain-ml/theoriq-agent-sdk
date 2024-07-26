"""
execute.py

Types and functions used by an Agent when executing a theoriq request
"""

from typing import Callable

from theoriq.facts import TheoriqCost, Currency
from theoriq.schemas import ExecuteRequestBody, DialogItem
from theoriq.types import RequestBiscuit


class ExecuteRequest:
    """
    This class encapsulates the necessary details retrieved from a request to the `execute` endpoint.

    Attributes:
        body (ExecuteRequestBody): Encapsulates the payload sent to the 'execute' endpoint.
        biscuit (RequestBiscuit): Holds the authentication information sent to the 'execute' endpoint.
    """

    def __init__(self, body: ExecuteRequestBody, biscuit: RequestBiscuit) -> None:
        self.body = body
        self.biscuit = biscuit


class ExecuteResponse:
    """
    Represents the result of executing a theoriq request.

    Attributes:
        body (DialogItem): The body to encapsulate in the response payload.
        cost (TheoriqCost): Cost of the processing of the request.
        status_code (int, optional): The status code of the response.
    """

    def __init__(
        self, body: DialogItem, cost: TheoriqCost = TheoriqCost.zero(Currency.USDC), status_code: int = 200
    ) -> None:
        self.body = body
        self.theoriq_cost = cost
        self.status_code = status_code


ExecuteFn = Callable[[ExecuteRequest], ExecuteResponse]
