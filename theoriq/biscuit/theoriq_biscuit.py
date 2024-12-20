from __future__ import annotations

import abc
from typing import Any, Dict, Generic, TypeVar
from uuid import UUID

from biscuit_auth import Authorizer, Biscuit, BlockBuilder, Fact, KeyPair, PrivateKey, PublicKey, Rule

from theoriq.biscuit import PayloadHash
from theoriq.biscuit.agent_address import AgentAddress
from theoriq.biscuit.utils import from_base64_token, verify_address

# Define a type variable
T = TypeVar("T")


class TheoriqFactBase(abc.ABC, Generic[T]):
    """Base class for facts contained in a biscuit"""

    @classmethod
    def from_biscuit(cls, theoriq_biscuit: TheoriqBiscuit) -> T:
        """Extract facts from a biscuit"""
        rule = cls.biscuit_rule()

        authorizer = Authorizer()
        authorizer.add_token(theoriq_biscuit.biscuit)
        facts = authorizer.query(rule)

        if len(facts) == 0:
            raise ValueError("No facts found in current biscuit")

        try:
            return cls.from_fact(facts[0])
        except Exception as e:
            raise ValueError("Missing information") from e

    @classmethod
    @abc.abstractmethod
    def biscuit_rule(cls) -> Rule:
        pass

    @classmethod
    @abc.abstractmethod
    def from_fact(cls, fact: Fact) -> T:
        pass

    @abc.abstractmethod
    def to_fact(self) -> Fact:
        pass

    def to_block_builder(self) -> BlockBuilder:
        """Convert facts to a biscuit block"""
        fact = self.to_fact()
        block_builder = BlockBuilder("")
        block_builder.add_fact(fact)
        return block_builder


class RequestFact(TheoriqFactBase):
    """`theoriq:request` fact"""

    def __init__(self, request_id: UUID, body_hash, from_addr: str | AgentAddress, to_addr: str) -> None:
        super().__init__()
        self.request_id = request_id
        self.body_hash = body_hash
        self.from_addr = from_addr if isinstance(from_addr, str) else from_addr.address
        self.to_addr = verify_address(to_addr)

    @classmethod
    def biscuit_rule(cls) -> Rule:
        return Rule(
            "data($req_id, $body_hash, $from_addr, $target_addr) <- theoriq:request($req_id, $body_hash, $from_addr, $target_addr)"
        )

    @classmethod
    def from_fact(cls, fact: Fact) -> RequestFact:
        [req_id, body_hash, from_addr, to_addr] = fact.terms
        return cls(req_id, body_hash, from_addr, to_addr)

    def to_fact(self) -> Fact:
        return Fact(
            "theoriq:request({req_id}, {body_hash}, {from_addr}, {to_addr})",
            {
                "req_id": str(self.request_id),
                "body_hash": str(self.body_hash),
                "from_addr": self.from_addr,
                "to_addr": self.to_addr,
            },
        )


class ResponseFact(TheoriqFactBase):
    """`theoriq:response` fact"""

    def __init__(self, request_id: UUID, body_hash: PayloadHash, to_addr: str) -> None:
        super().__init__()
        self.request_id = request_id
        self._body_hash = body_hash
        self.to_addr = to_addr

    @classmethod
    def biscuit_rule(cls) -> Rule:
        return Rule("data($req_id, $body_hash, $target_addr) <- theoriq:response($req_id, $body_hash, $target_addr)")

    @classmethod
    def from_fact(cls, fact: Fact) -> ResponseFact:
        [req_id, body_hash, to_addr] = fact.terms
        return cls(req_id, body_hash, to_addr)

    def to_fact(self) -> Fact:
        return Fact(
            "theoriq:response({req_id}, {body_hash}, {to_addr})",
            {"req_id": str(self.request_id), "body_hash": str(self._body_hash), "to_addr": self.to_addr},
        )


class TheoriqBiscuit:
    """Base class for biscuits used in Theoriq protocol"""

    def __init__(self, biscuit: Biscuit) -> None:
        self.biscuit = biscuit

    @classmethod
    def from_token(cls, token: str, public_key: str) -> TheoriqBiscuit:
        public_key = public_key.removeprefix("0x")
        biscuit = from_base64_token(token, PublicKey.from_hex(public_key))
        return cls(biscuit)

    def to_base64(self) -> str:
        return self.biscuit.to_base64()

    def to_headers(self) -> Dict[str, Any]:
        return {
            "Content-Type": "application/json",
            "Authorization": "bearer " + self.biscuit.to_base64(),
        }

    def attenuate(self, agent_pk: PrivateKey, fact: TheoriqFactBase) -> TheoriqBiscuit:
        agent_kp = KeyPair.from_private_key(agent_pk)
        block_builder = fact.to_block_builder()
        attenuated_biscuit = self.biscuit.append_third_party_block(agent_kp, block_builder)  # type: ignore
        return TheoriqBiscuit(attenuated_biscuit)
