"""
Theoriq biscuit facts
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from uuid import UUID
from biscuit_auth import Fact, Rule, Biscuit, Authorizer, BlockBuilder


class Currency(Enum):
    USDC = "USDC"
    USDT = "USDT"

    @staticmethod
    def from_value(value: Any):
        try:
            return Currency(str(value))
        except ValueError as e:
            raise ValueError(f"'{value}' is not a valid Currency") from e


class TheoriqRequest:
    """`theoriq:request` fact"""

    def __init__(self, *, body_hash: str, from_addr: str, to_addr: str) -> None:
        self.body_hash = body_hash
        self.from_addr = from_addr
        self.to_addr = to_addr

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
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

    def __init__(self, *, amount: str, currency: Optional[Currency] = None, voucher: str) -> None:
        self.amount = amount
        if len(amount) > 0 and currency is None:
            raise ValueError("Invalid budget: currency must be specified if amount is specified")
        self.currency = currency
        self.voucher = voucher

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def to_fact(self, req_id: str) -> Fact:
        """Convert to a biscuit fact"""
        return Fact(
            "theoriq:budget({req_id}, {amount}, {currency}, {voucher})",
            {
                "req_id": req_id,
                "amount": self.amount,
                "currency": self.currency.value if self.currency else "",
                "voucher": self.voucher,
            },
        )

    @classmethod
    def from_amount(cls, *, amount: str, currency: Currency) -> TheoriqBudget:
        return cls(amount=amount, currency=currency, voucher="")

    @classmethod
    def from_voucher(cls, *, voucher: str) -> TheoriqBudget:
        return cls(amount="", currency=None, voucher=voucher)


class RequestFacts:
    """Required facts inside the request biscuit"""

    def __init__(self, req_id: UUID, request: TheoriqRequest, budget: TheoriqBudget) -> None:
        self.req_id = req_id
        self.request = request
        self.budget = budget

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    @staticmethod
    def from_biscuit(biscuit: Biscuit) -> RequestFacts:
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
        theoriq_request = TheoriqRequest(body_hash=body_hash, from_addr=from_addr, to_addr=to_addr)
        theoriq_budget = TheoriqBudget(amount=amount, currency=Currency.from_value(currency), voucher=voucher)

        return RequestFacts(request_id, theoriq_request, theoriq_budget)

    def to_block(self) -> BlockBuilder:
        """Construct a biscuit block using the requestfacts"""
        block_builder = BlockBuilder("")
        request_id = str(self.req_id)
        block_builder.add_fact(self.request.to_fact(request_id))
        block_builder.add_fact(self.budget.to_fact(request_id))

        return block_builder

    def __str__(self):
        return f"req_id={self.req_id}, request={self.request}, budget={self.budget}"


class TheoriqResponse:
    """`theoriq:response` fact"""

    def __init__(self, *, body_hash: str, to_addr: str) -> None:
        self.body_hash = body_hash
        self.to_addr = to_addr

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def to_fact(self, req_id: str) -> Fact:
        """Convert to a biscuit fact"""
        return Fact(
            "theoriq:response({req_id}, {body_hash}, {to_addr})",
            {"req_id": req_id, "body_hash": self.body_hash, "to_addr": self.to_addr},
        )


class TheoriqCost:
    """
    Biscuit fact representing the cost for the execution of an 'execute' request.
    """

    def __init__(self, *, amount: str, currency: Currency) -> None:
        self.amount = amount
        self.currency = currency

    @classmethod
    def zero(cls, currency: Currency) -> TheoriqCost:
        """Return a zero cost"""
        return cls(amount="0", currency=currency)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def to_fact(self, request_id: str) -> Fact:
        """Convert to a biscuit fact"""
        return Fact(
            "theoriq:cost({req_id}, {amount}, {currency})",
            {"req_id": request_id, "amount": self.amount, "currency": self.currency.value},
        )

    def __str__(self):
        return f"TheoriqCost(amount={self.amount}, currency={self.currency.value})"


class ResponseFacts:
    """Required facts inside the response biscuit"""

    def __init__(self, req_id: UUID, response: TheoriqResponse, cost: TheoriqCost):
        self.req_id = req_id
        self.response = response
        self.cost = cost

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def __str__(self):
        return f"req_id={self.req_id}, response={self.response}, cost={self.cost}"

    @staticmethod
    def from_biscuit(biscuit: Biscuit) -> ResponseFacts:
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
        theoriq_response = TheoriqResponse(body_hash=body_hash, to_addr=to_addr)
        theoriq_cost = TheoriqCost(amount=amount, currency=Currency.from_value(currency))

        return ResponseFacts(request_id, theoriq_response, theoriq_cost)

    def to_block(self) -> BlockBuilder:
        """Construct a biscuit block using the response facts"""
        block_builder = BlockBuilder("")
        request_id = str(self.req_id)
        block_builder.add_fact(self.response.to_fact(request_id))
        block_builder.add_fact(self.cost.to_fact(request_id))

        return block_builder
