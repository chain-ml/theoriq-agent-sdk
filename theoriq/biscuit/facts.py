"""
Theoriq biscuit facts
"""

from __future__ import annotations

import abc
import itertools
from typing import Generic, List, TypeVar
from uuid import UUID

from biscuit_auth import BlockBuilder, Fact, Rule
from typing_extensions import Self

from theoriq.types import Currency

from .agent_address import AgentAddress
from .payload_hash import PayloadHash
from .utils import verify_address


class TheoriqFactBase(abc.ABC):
    """Base class for facts contained in a biscuit"""

    @classmethod
    @abc.abstractmethod
    def biscuit_rule(cls) -> Rule:
        pass

    @classmethod
    @abc.abstractmethod
    def from_fact(cls, fact: Fact) -> Self:
        pass

    @abc.abstractmethod
    def to_facts(self) -> List[Fact]:
        pass

    def to_block_builder(self) -> BlockBuilder:
        """Convert facts to a biscuit block"""
        block_builder = BlockBuilder("")
        for fact in self.to_facts():
            block_builder.add_fact(fact)
        return block_builder


class SubjectFact(TheoriqFactBase):
    """`theoriq:subject` fact"""

    def __init__(self, *, agent_id: str):
        super().__init__()
        self.agent_id = agent_id

    @classmethod
    def biscuit_rule(cls) -> Rule:
        return Rule("""address($address) <- theoriq:subject("agent", $address)""")

    @classmethod
    def from_fact(cls, fact: Fact) -> Self:
        [address] = fact.terms
        return cls(agent_id=address)

    def to_facts(self) -> list[Fact]:
        fact = Fact(
            """theoriq:subject("agent", {agent_id})""",
            {"agent_id": self.agent_id},
        )
        return [fact]


class RequestFact(TheoriqFactBase):
    """`theoriq:request` fact"""

    def __init__(
        self, *, request_id: UUID, body_hash: PayloadHash, from_addr: str | AgentAddress, to_addr: str
    ) -> None:
        super().__init__()
        self.request_id = request_id
        self.body_hash = body_hash
        self.from_addr = from_addr if isinstance(from_addr, str) else from_addr.address
        self.to_addr = verify_address(to_addr)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    @classmethod
    def biscuit_rule(cls) -> Rule:
        return Rule(
            "data($req_id, $body_hash, $from_addr, $target_addr) <- theoriq:request($req_id, $body_hash, $from_addr, $target_addr)"
        )

    @classmethod
    def from_fact(cls, fact: Fact) -> Self:
        [req_id, body_hash, from_addr, to_addr] = fact.terms
        return cls(request_id=req_id, body_hash=body_hash, from_addr=from_addr, to_addr=to_addr)

    def to_facts(self) -> List[Fact]:
        fact = Fact(
            "theoriq:request({req_id}, {body_hash}, {from_addr}, {to_addr})",
            {
                "req_id": str(self.request_id),
                "body_hash": str(self.body_hash),
                "from_addr": self.from_addr,
                "to_addr": self.to_addr,
            },
        )
        return [fact]


class BudgetFact(TheoriqFactBase):
    """`theoriq:budget` fact"""

    def __init__(self, *, request_id: UUID, amount: str, currency: str, voucher: str) -> None:
        self.request_id = request_id
        self.amount = amount
        self.currency = currency
        self.voucher = voucher

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    @classmethod
    def biscuit_rule(cls) -> Rule:
        return Rule(
            "data($req_id, $amount, $currency, $voucher) <- theoriq:budget($req_id, $amount, $currency, $voucher)"
        )

    @classmethod
    def from_fact(cls, fact: Fact) -> BudgetFact:
        [req_id, amount, currency, voucher] = fact.terms
        return cls(request_id=req_id, amount=amount, currency=currency, voucher=voucher)

    def to_facts(self) -> List[Fact]:
        """Convert to a biscuit fact"""
        fact = Fact(
            "theoriq:budget({req_id}, {amount}, {currency}, {voucher})",
            {
                "req_id": str(self.request_id),
                "amount": self.amount,
                "currency": self.currency,
                "voucher": self.voucher,
            },
        )
        return [fact]


class ResponseFact(TheoriqFactBase):
    """`theoriq:response` fact"""

    def __init__(self, *, request_id: UUID, body_hash: PayloadHash, to_addr: str) -> None:
        super().__init__()
        self.request_id = request_id
        self.body_hash = body_hash
        self.to_addr = to_addr

    @classmethod
    def biscuit_rule(cls) -> Rule:
        return Rule("data($req_id, $body_hash, $target_addr) <- theoriq:response($req_id, $body_hash, $target_addr)")

    @classmethod
    def from_fact(cls, fact: Fact) -> ResponseFact:
        [req_id, body_hash, to_addr] = fact.terms
        return cls(request_id=req_id, body_hash=body_hash, to_addr=to_addr)

    def to_facts(self) -> List[Fact]:
        fact = Fact(
            "theoriq:response({req_id}, {body_hash}, {to_addr})",
            {"req_id": str(self.request_id), "body_hash": str(self.body_hash), "to_addr": self.to_addr},
        )
        return [fact]


class CostFact(TheoriqFactBase):
    """`theoriq:cost` fact"""

    def __init__(self, *, request_id: UUID, amount: str, currency: str) -> None:
        super().__init__()
        self.request_id = request_id
        self.amount = amount
        self.currency = currency

    @classmethod
    def biscuit_rule(cls) -> Rule:
        return Rule("data($req_id, $amount, $currency) <- theoriq:cost($req_id, $amount, $currency)")

    @classmethod
    def from_fact(cls, fact: Fact) -> CostFact:
        [req_id, amount, currency] = fact.terms
        return cls(request_id=req_id, amount=amount, currency=currency)

    def to_facts(self) -> List[Fact]:
        fact = Fact(
            "theoriq:cost({req_id}, {amount}, {currency})",
            {"req_id": str(self.request_id), "amount": self.amount, "currency": self.currency},
        )
        return [fact]


class ExecuteRequestFacts(TheoriqFactBase):
    """`theoriq:request` & `theoriq:budget` facts"""

    def __init__(self, *, request: RequestFact, budget: BudgetFact) -> None:
        assert request.request_id == budget.request_id
        self.request = request
        self.budget = budget

    @classmethod
    def biscuit_rule(cls) -> Rule:
        return Rule(
            """
            data($req_id, $body_hash, $from_addr, $target_addr, $amount, $currency, $voucher) <- theoriq:request($req_id, $body_hash, $from_addr, $target_addr), theoriq:budget($req_id, $amount, $currency, $voucher)
            """
        )

    @classmethod
    def from_fact(cls, fact: Fact) -> Self:
        [req_id, body_hash, from_addr, to_addr, amount, currency, voucher] = fact.terms
        request = RequestFact(request_id=req_id, body_hash=body_hash, from_addr=from_addr, to_addr=to_addr)
        budget = BudgetFact(request_id=req_id, amount=amount, currency=currency, voucher=voucher)
        return cls(request=request, budget=budget)

    def to_facts(self) -> List[Fact]:
        facts = [self.request.to_facts(), self.budget.to_facts()]
        return list(itertools.chain.from_iterable(facts))


class ExecuteResponseFacts(TheoriqFactBase):
    """`theoriq:response` & `theoriq:cost` facts"""

    def __init__(self, *, response: ResponseFact, cost: CostFact) -> None:
        self.response = response
        self.cost = cost

    @classmethod
    def biscuit_rule(cls) -> Rule:
        return Rule(
            """
            data($req_id, $body_hash, $target_addr, $amount, $currency) <- theoriq:response($req_id, $body_hash, $target_addr), theoriq:cost($req_id, $amount, $currency)
            """
        )

    @classmethod
    def from_fact(cls, fact: Fact) -> Self:
        [req_id, body_hash, to_addr, amount, currency] = fact.terms
        response = ResponseFact(request_id=req_id, body_hash=body_hash, to_addr=to_addr)
        cost = CostFact(request_id=req_id, amount=amount, currency=currency)
        return cls(response=response, cost=cost)

    def to_facts(self) -> List[Fact]:
        facts = [self.response.to_facts(), self.cost.to_facts()]
        return list(itertools.chain.from_iterable(facts))


T = TypeVar("T", bound=TheoriqFactBase)


class FactConvertibleBase(abc.ABC, Generic[T]):
    @abc.abstractmethod
    def to_theoriq_fact(self, request_id: UUID) -> T:
        pass

    @classmethod
    @abc.abstractmethod
    def from_theoriq_fact(cls, fact: T) -> Self:
        pass


class TheoriqRequest(FactConvertibleBase[RequestFact]):
    def __init__(self, *, body_hash: PayloadHash, from_addr: str | AgentAddress, to_addr: str) -> None:
        self.body_hash = body_hash
        self.from_addr = from_addr if isinstance(from_addr, str) else from_addr.address
        self.to_addr = verify_address(to_addr)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def to_theoriq_fact(self, request_id: UUID) -> RequestFact:
        return RequestFact(
            request_id=request_id, body_hash=self.body_hash, from_addr=self.from_addr, to_addr=self.to_addr
        )

    @classmethod
    def from_theoriq_fact(cls, fact: RequestFact) -> TheoriqRequest:
        return cls(body_hash=fact.body_hash, from_addr=fact.from_addr, to_addr=fact.to_addr)

    @classmethod
    def from_body(cls, body: bytes, from_addr: str | AgentAddress, to_addr: str) -> TheoriqRequest:
        """Create a response fact from a response body"""
        body_hash = PayloadHash(body)
        return cls(body_hash=body_hash, from_addr=from_addr, to_addr=to_addr)

    def __str__(self):
        return f"TheoriqRequest(body_hash={self.body_hash}, from_addr={self.from_addr}, to_addr={self.to_addr})"


class TheoriqBudget(FactConvertibleBase[BudgetFact]):

    def __init__(self, *, amount: str | int, currency: Currency | str, voucher: str) -> None:
        self.amount = str(amount)
        self.currency: Currency = currency if isinstance(currency, Currency) else Currency(currency)
        self.voucher = voucher

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def __str__(self):
        if len(self.voucher) == 0:
            return f"TheoriqBudget(amount={self.amount}, currency={self.currency})"

        currency = self.currency.value if self.currency else None
        return f"TheoriqBudget(amount={self.amount}, currency={currency}, voucher={self.voucher})"

    def to_theoriq_fact(self, request_id: UUID) -> BudgetFact:
        return BudgetFact(request_id=request_id, amount=self.amount, currency=self.currency.value, voucher=self.voucher)

    @classmethod
    def from_theoriq_fact(cls, fact: BudgetFact) -> Self:
        return cls(amount=fact.amount, currency=Currency(fact.currency), voucher=fact.voucher)

    @classmethod
    def from_amount(cls, *, amount: str | int, currency: Currency) -> TheoriqBudget:
        return cls(amount=amount, currency=currency, voucher="")

    @classmethod
    def empty(cls) -> TheoriqBudget:
        return cls(amount=0, currency=Currency.USDC, voucher="")

    @classmethod
    def from_voucher(cls, *, voucher: str) -> TheoriqBudget:
        return cls(amount="", currency=Currency.USDC, voucher=voucher)


class TheoriqResponse(FactConvertibleBase[ResponseFact]):
    def __init__(self, *, body_hash: PayloadHash, to_addr: str) -> None:
        self._body_hash = body_hash
        self.to_addr = to_addr

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def to_theoriq_fact(self, request_id: UUID) -> ResponseFact:
        return ResponseFact(request_id=request_id, body_hash=self._body_hash, to_addr=self.to_addr)

    @classmethod
    def from_theoriq_fact(cls, fact: ResponseFact) -> Self:
        return cls(body_hash=fact.body_hash, to_addr=fact.to_addr)

    def __str__(self):
        return f"TheoriqResponse(body_hash={self._body_hash}, to_addr={self.to_addr})"

    @classmethod
    def from_body(cls, body: bytes, to_addr: str) -> TheoriqResponse:
        """Create a response fact from a response body"""
        body_hash = PayloadHash(body)
        return cls(body_hash=body_hash, to_addr=to_addr)


class TheoriqCost(FactConvertibleBase[CostFact]):
    def __init__(self, *, amount: str | int, currency: str | Currency) -> None:
        self.amount = str(amount)
        self.currency = currency if isinstance(currency, Currency) else Currency(currency)

    @classmethod
    def zero(cls, currency: Currency) -> TheoriqCost:
        """Return a zero cost"""
        return cls(amount=0, currency=currency)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def to_theoriq_fact(self, request_id: UUID) -> CostFact:
        return CostFact(request_id=request_id, amount=self.amount, currency=self.currency.value)

    @classmethod
    def from_theoriq_fact(cls, fact: CostFact) -> Self:
        return cls(amount=fact.amount, currency=Currency(fact.currency))

    def __str__(self):
        return f"TheoriqCost(amount={self.amount}, currency={self.currency.value})"
