"""
execute.py

Types and functions used by an Agent when executing a theoriq request
"""

from typing import Callable

from theoriq.facts import TheoriqCost
from theoriq.schemas import ExecuteRequestBody, DialogItem
from theoriq.types import RequestBiscuit


class ExecuteRequest:
    """
    This class encapsulates the necessary details retrieved from a request to the `execute` endpoint.

    Attributes:
        body (ExecuteRequestBody): Encapsulates the payload sent to the 'execute' endpoint.
        biscuit (RequestBiscuit): Holds the authentication information sent to the 'execute' endpoint.
    """

    def __init__(self, body: ExecuteRequestBody, biscuit: RequestBiscuit):
        self.body = body
        self.biscuit = biscuit


class ExecuteResponse:
    """
    Represents the result of executing a theoriq request.

    Attributes:
        body (DialogItem): The body to encapsulate in the response payload.
        theoriq_cost (TheoriqCost): Cost of the processing of the request.
        status_code (int, optional): The status code of the response.
    """

    def __init__(self, body: DialogItem, theoriq_cost: TheoriqCost = TheoriqCost.zero("USDC"), status_code: int = 200):
        self.body = body
        self.theoriq_cost = theoriq_cost
        self.status_code = status_code


ExecuteFn = Callable[[ExecuteRequest], ExecuteResponse]
