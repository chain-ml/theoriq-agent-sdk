"""
Theoriq biscuit facts
"""

from uuid import UUID
from biscuit_auth import Fact, Rule, Biscuit, Authorizer, BlockBuilder


class TheoriqRequest:
    """`theoriq:request` fact"""

    def __init__(self, body_hash: str, from_addr: str, to_addr: str):
        self.body_hash = body_hash
        self.from_addr = from_addr
        self.to_addr = to_addr

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def to_fact(self, req_id: str) -> Fact:
        """Convert to a biscuit fact"""
        return Fact(
            "theoriq:request({req_id}, {body_hash}, {from_addr}, {to_addr})",
            {
                "req_id": req_id,
                "body_hash": self.body_hash,
                "from_addr": self.from_addr,
                "to_addr": self.to_addr,
            },
        )


class TheoriqBudget:
    """`theoriq:budget` fact"""

    def __init__(self, amount: str, currency: str, voucher: str):
        self.amount = amount
        self.currency = currency
        self.voucher = voucher

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def to_fact(self, req_id: str) -> Fact:
        """Convert to a biscuit fact"""
        return Fact(
            "theoriq:budget({req_id}, {amount}, {currency}, {voucher})",
            {
                "req_id": req_id,
                "amount": self.amount,
                "currency": self.currency,
                "voucher": self.voucher,
            },
        )


class RequestFacts:
    """Required facts inside the request biscuit"""

    def __init__(self, req_id: UUID, request: TheoriqRequest, budget: TheoriqBudget):
        self.req_id = req_id
        self.request = request
        self.budget = budget

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    @staticmethod
    def from_biscuit(biscuit: Biscuit) -> "RequestFacts":
        """Read request facts from biscuit"""

        rule = Rule(
            """
            data($req_id, $body_hash, $from_addr, $target_addr, $amount, $currency, $voucher) <- theoriq:request($req_id, $body_hash, $from_addr, $target_addr), theoriq:budget($req_id, $amount, $currency, $voucher)
            """
        )

        authorizer = Authorizer()
        authorizer.add_token(biscuit)
        facts = authorizer.query(rule)

        [req_id, body_hash, from_addr, to_addr, amount, currency, voucher] = facts[0].terms
        request_id = UUID(req_id)
        theoriq_req = TheoriqRequest(body_hash, from_addr, to_addr)
        theoriq_budget = TheoriqBudget(amount, currency, voucher)

        return RequestFacts(request_id, theoriq_req, theoriq_budget)

    def to_block(self) -> BlockBuilder:
        """Construct a biscuit block using the requestfacts"""
        block_builder = BlockBuilder("")
        request_id = str(self.req_id)
        block_builder.add_fact(self.request.to_fact(request_id))
        block_builder.add_fact(self.budget.to_fact(request_id))

        return block_builder


class TheoriqResponse:
    """`theoriq:response` fact"""

    def __init__(self, body_hash: str, to_addr: str):
        self.body_hash = body_hash
        self.to_addr = to_addr

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def to_fact(self, req_id: str) -> Fact:
        """Convert to a biscuit fact"""
        return Fact(
            "theoriq:response({req_id}, {body_hash}, {to_addr})",
            {"req_id": req_id, "body_hash": self.body_hash, "to_addr": self.to_addr},
        )


class TheoriqCost:
    """`theoriq:cost` fact"""

    def __init__(self, amount: str, currency: str):
        self.amount = amount
        self.currency = currency

    @classmethod
    def zero(cls, currency: str) -> "TheoriqCost":
        """Return a zero cost"""
        return cls("0", currency)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def to_fact(self, req_id: str) -> Fact:
        """Convert to a biscuit fact"""
        return Fact(
            "theoriq:cost({req_id}, {amount}, {currency})",
            {"req_id": req_id, "amount": self.amount, "currency": self.currency},
        )


class ResponseFacts:
    """Required facts inside the response biscuit"""

    def __init__(self, req_id: UUID, response: TheoriqResponse, cost: TheoriqCost):
        self.req_id = req_id
        self.response = response
        self.cost = cost

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    @staticmethod
    def from_biscuit(biscuit: Biscuit) -> "ResponseFacts":
        """Read response facts from biscuit"""
        rule = Rule(
            """
            data($req_id, $body_hash, $target_addr, $amount, $currency) <- theoriq:response($req_id, $body_hash, $target_addr), theoriq:cost($req_id, $amount, $currency)
            """
        )

        authorizer = Authorizer()
        authorizer.add_token(biscuit)
        facts = authorizer.query(rule)

        [req_id, body_hash, to_addr, amount, currency] = facts[0].terms
        request_id = UUID(req_id)
        theoriq_resp = TheoriqResponse(body_hash, to_addr)
        theoriq_cost = TheoriqCost(amount, currency)

        return ResponseFacts(request_id, theoriq_resp, theoriq_cost)

    def to_block(self) -> BlockBuilder:
        """Construct a biscuit block using the response facts"""
        block_builder = BlockBuilder("")
        request_id = str(self.req_id)
        block_builder.add_fact(self.response.to_fact(request_id))
        block_builder.add_fact(self.cost.to_fact(request_id))

        return block_builder
