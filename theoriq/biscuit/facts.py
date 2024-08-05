"""
Theoriq biscuit facts
"""

from __future__ import annotations

import abc
import uuid
from typing import Optional
from uuid import UUID

from biscuit_auth import Authorizer, Biscuit, BlockBuilder, Fact, Rule
from theoriq.types.currency import Currency
from theoriq.utils import hash_body, verify_address


class FactConvertibleBase(abc.ABC):
    @abc.abstractmethod
    def to_fact(self, req_id: str) -> Fact:
        pass


class TheoriqRequest(FactConvertibleBase):
    """`theoriq:request` fact"""

    def __init__(self, *, body_hash: str, from_addr: str, to_addr: str) -> None:
        self.body_hash = body_hash
        self.from_addr = from_addr
        self.to_addr = verify_address(to_addr)

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

    @classmethod
    def from_body(cls, body: bytes, from_addr: str, to_addr: str) -> TheoriqRequest:
        """Create a response fact from a response body"""
        body_hash = hash_body(body)
        return cls(body_hash=body_hash, from_addr=from_addr, to_addr=to_addr)


class TheoriqBudget(FactConvertibleBase):
    """`theoriq:budget` fact"""

    def __init__(self, *, amount: str | int, currency: Optional[Currency] = None, voucher: str) -> None:
        self.amount = str(amount)
        if len(self.amount) > 0 and currency is None:
            raise ValueError("Invalid budget: currency must be specified if amount is specified")
        self.currency = currency
        self.voucher = voucher

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def __str__(self):
        currency = self.currency.value if self.currency else None
        return f"TheoriqBudget(amount={self.amount}, currency={currency}, voucher={self.voucher})"

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
    def from_amount(cls, *, amount: str | int, currency: Currency) -> TheoriqBudget:
        return cls(amount=amount, currency=currency, voucher="")

    @classmethod
    def empty(cls) -> TheoriqBudget:
        return cls(amount=0, currency=Currency.USDC, voucher="")

    @classmethod
    def from_voucher(cls, *, voucher: str) -> TheoriqBudget:
        return cls(amount="", currency=None, voucher=voucher)


class TheoriqResponse(FactConvertibleBase):
    """`theoriq:response` fact"""

    def __init__(self, *, body_hash: str, to_addr: str) -> None:
        self.body_hash = body_hash
        self.to_addr = to_addr

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def to_fact(self, req_id: str | UUID) -> Fact:
        """Convert to a biscuit fact"""
        return Fact(
            "theoriq:response({req_id}, {body_hash}, {to_addr})",
            {"req_id": str(req_id), "body_hash": self.body_hash, "to_addr": self.to_addr},
        )

    def __str__(self):
        return f"TheoriqResponse(body_hash={self.body_hash}, to_addr={self.to_addr})"

    @classmethod
    def from_body(cls, body: bytes, to_addr: str) -> TheoriqResponse:
        """Create a response fact from a response body"""
        body_hash = hash_body(body)
        return cls(body_hash=body_hash, to_addr=to_addr)


class TheoriqCost(FactConvertibleBase):
    """
    Biscuit fact representing the cost for the execution of an 'execute' request.
    """

    def __init__(self, *, amount: str | int, currency: Currency) -> None:
        self.amount = str(amount)
        self.currency = currency

    @classmethod
    def zero(cls, currency: Currency) -> TheoriqCost:
        """Return a zero cost"""
        return cls(amount=0, currency=currency)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def to_fact(self, request_id: str | UUID) -> Fact:
        """Convert to a biscuit fact"""
        return Fact(
            "theoriq:cost({req_id}, {amount}, {currency})",
            {"req_id": str(request_id), "amount": self.amount, "currency": self.currency.value},
        )

    def __str__(self):
        return f"TheoriqCost(amount={self.amount}, currency={self.currency.value})"


class RequestFacts:
    """Required facts inside the request biscuit"""

    def __init__(self, request_id: UUID | str, request: TheoriqRequest, budget: TheoriqBudget) -> None:
        self.req_id = request_id if isinstance(request_id, UUID) else UUID(request_id)
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
        theoriq_request = TheoriqRequest(body_hash=body_hash, from_addr=from_addr, to_addr=to_addr)
        theoriq_budget = TheoriqBudget(amount=amount, currency=Currency.from_value(currency), voucher=voucher)

        return RequestFacts(req_id, theoriq_request, theoriq_budget)

    def to_block_builder(self) -> BlockBuilder:
        """Construct a biscuit block builder using the facts"""
        block_builder = BlockBuilder("")
        request_id = str(self.req_id)
        block_builder.add_fact(self.request.to_fact(request_id))
        block_builder.add_fact(self.budget.to_fact(request_id))

        return block_builder

    def __str__(self):
        return f"RequestFacts(req_id={self.req_id}, request={self.request}, budget={self.budget})"

    @classmethod
    def default(cls, body: bytes, from_addr: str, to_addr: str) -> RequestFacts:
        theoriq_request = TheoriqRequest.from_body(body=body, from_addr=from_addr, to_addr=to_addr)
        return cls(uuid.uuid4(), theoriq_request, TheoriqBudget.empty())


class ResponseFacts:
    """Required facts inside the response biscuit"""

    def __init__(self, request_id: UUID | str, response: TheoriqResponse, cost: TheoriqCost):
        self.req_id = request_id if isinstance(request_id, UUID) else UUID(request_id)
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
        theoriq_response = TheoriqResponse(body_hash=body_hash, to_addr=to_addr)
        theoriq_cost = TheoriqCost(amount=amount, currency=Currency.from_value(currency))

        return ResponseFacts(req_id, theoriq_response, theoriq_cost)

    def to_block_builder(self) -> BlockBuilder:
        """Construct a biscuit block using the response facts"""
        block_builder = BlockBuilder("")
        block_builder.add_fact(self.response.to_fact(self.req_id))
        block_builder.add_fact(self.cost.to_fact(self.req_id))

        return block_builder
