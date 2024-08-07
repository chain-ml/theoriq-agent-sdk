"""
Theoriq biscuit facts
"""

from __future__ import annotations

import abc
from typing import Optional
from uuid import UUID

from biscuit_auth import Fact  # pylint: disable=E0611
from theoriq.types.currency import Currency
from theoriq.utils import hash_body, verify_address


class FactConvertibleBase(abc.ABC):
    @abc.abstractmethod
    def to_fact(self, request_id: str) -> Fact:
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

    def to_fact(self, request_id: str) -> Fact:
        """Convert to a biscuit fact"""
        return Fact(
            "theoriq:request({req_id}, {body_hash}, {from_addr}, {to_addr})",
            {
                "req_id": request_id,
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

    def __str__(self):
        return f"TheoriqRequest(body_hash={self.body_hash}, from_addr={self.from_addr}, to_addr={self.to_addr})"


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
        if len(self.voucher) == 0:
            return f"TheoriqBudget(amount={self.amount}, currency={self.currency})"

        currency = self.currency.value if self.currency else None
        return f"TheoriqBudget(amount={self.amount}, currency={currency}, voucher={self.voucher})"

    def to_fact(self, request_id: str) -> Fact:
        """Convert to a biscuit fact"""
        return Fact(
            "theoriq:budget({req_id}, {amount}, {currency}, {voucher})",
            {
                "req_id": request_id,
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

    def to_fact(self, request_id: str | UUID) -> Fact:
        """Convert to a biscuit fact"""
        return Fact(
            "theoriq:response({req_id}, {body_hash}, {to_addr})",
            {"req_id": str(request_id), "body_hash": self.body_hash, "to_addr": self.to_addr},
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
