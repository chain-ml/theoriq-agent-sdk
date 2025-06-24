"""
Theoriq biscuit facts
"""

from __future__ import annotations

import abc
import itertools
import time
from typing import Generic, List, TypeVar
from uuid import UUID

from biscuit_auth import BlockBuilder, Fact, Rule
from typing_extensions import Self

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


class ExpiresAtFact(TheoriqFactBase):
    """`theoriq:expire_at` fact"""

    def __init__(self, *, expires_at: int) -> None:
        super().__init__()
        self.expires_at = expires_at

    @classmethod
    def biscuit_rule(cls) -> Rule:
        return Rule("expires_at($timestamp) <- theoriq:expires_at($timestamp)")

    @classmethod
    def from_fact(cls, fact: Fact) -> Self:
        [expires_at] = fact.terms
        return cls(expires_at=expires_at)

    def to_facts(self) -> List[Fact]:
        fact = Fact("theoriq:expires_at({expires_at})", {"expires_at": self.expires_at})
        return [fact]

    @classmethod
    def from_lifetime_duration(cls, duration_in_second: int) -> Self:
        timestamp = int(time.time()) + duration_in_second
        return cls(expires_at=timestamp)


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

    def to_facts(self) -> List[Fact]:
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


class ExecuteRequestFacts(TheoriqFactBase):
    """`theoriq:request` fact"""

    def __init__(self, *, request: RequestFact) -> None:
        self.request = request

    @classmethod
    def biscuit_rule(cls) -> Rule:
        return Rule(
            """
            data($req_id, $body_hash, $from_addr, $target_addr) <- theoriq:request($req_id, $body_hash, $from_addr, $target_addr)
            """
        )

    @classmethod
    def from_fact(cls, fact: Fact) -> Self:
        [req_id, body_hash, from_addr, to_addr] = fact.terms
        request = RequestFact(request_id=req_id, body_hash=body_hash, from_addr=from_addr, to_addr=to_addr)
        return cls(request=request)

    def to_facts(self) -> List[Fact]:
        facts = [self.request.to_facts()]
        return list(itertools.chain.from_iterable(facts))


class ExecuteResponseFacts(TheoriqFactBase):
    """`theoriq:response` fact"""

    def __init__(self, *, response: ResponseFact) -> None:
        self.response = response

    @classmethod
    def biscuit_rule(cls) -> Rule:
        return Rule(
            """
            data($req_id, $body_hash, $target_addr) <- theoriq:response($req_id, $body_hash, $target_addr)
            """
        )

    @classmethod
    def from_fact(cls, fact: Fact) -> Self:
        [req_id, body_hash, to_addr] = fact.terms
        response = ResponseFact(request_id=req_id, body_hash=body_hash, to_addr=to_addr)
        return cls(response=response)

    def to_facts(self) -> List[Fact]:
        facts = [self.response.to_facts()]
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

    def __str__(self) -> str:
        return f"TheoriqRequest(body_hash={self.body_hash}, from_addr={self.from_addr}, to_addr={self.to_addr})"


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

    def __str__(self) -> str:
        return f"TheoriqResponse(body_hash={self._body_hash}, to_addr={self.to_addr})"

    @classmethod
    def from_body(cls, body: bytes, to_addr: str) -> TheoriqResponse:
        """Create a response fact from a response body"""
        body_hash = PayloadHash(body)
        return cls(body_hash=body_hash, to_addr=to_addr)
