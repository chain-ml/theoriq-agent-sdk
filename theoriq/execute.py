"""Types and functions used by an Agent when execute a theoriq request"""

from typing import Callable

from theoriq.facts import TheoriqCost
from theoriq.schemas import ExecuteRequestBody, DialogItem
from theoriq.types import RequestBiscuit


class ExecuteRequest:
    """Request used when calling the `execute` endpoint"""

    def __init__(self, body: ExecuteRequestBody, biscuit: RequestBiscuit):
        self.body = body
        self.biscuit = biscuit


class ExecuteResponse:
    """Response to an `ExecuteRequest`"""

    def __init__(self, body: DialogItem, theoriq_cost: TheoriqCost = TheoriqCost.zero("USDC"), status_code: int = 200):
        self.body = body
        self.theoriq_cost = theoriq_cost
        self.status_code = status_code


ExecuteFn = Callable[[ExecuteRequest], ExecuteResponse]
