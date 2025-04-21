from __future__ import annotations

from typing import Any, Dict, Sequence, Type, TypeVar
from uuid import UUID

from biscuit_auth import Authorizer, Biscuit, BlockBuilder, KeyPair, PrivateKey, PublicKey

from theoriq.biscuit.facts import FactConvertibleBase, TheoriqFactBase
from theoriq.biscuit.utils import from_base64_token

T = TypeVar("T", bound=TheoriqFactBase)


class TheoriqBiscuit:
    """Base class for biscuits used in Theoriq protocol"""

    def __init__(self, biscuit: Biscuit) -> None:
        self.biscuit = biscuit

    @classmethod
    def from_token(cls, *, token: str, public_key: str) -> TheoriqBiscuit:
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

    def attenuate(self, fact: TheoriqFactBase) -> TheoriqBiscuit:
        attenuated_biscuit = self.biscuit.append(fact.to_block_builder())  # type: ignore
        return TheoriqBiscuit(attenuated_biscuit)

    def attenuate_third_party_block(self, agent_pk: PrivateKey, fact: TheoriqFactBase) -> TheoriqBiscuit:
        block_builder = fact.to_block_builder()
        return self._attenuate_third_party_block(agent_pk, block_builder)

    def attenuate_for_request(
        self, agent_pk: PrivateKey, request_id: UUID, facts: Sequence[FactConvertibleBase]
    ) -> TheoriqBiscuit:
        block_builder = BlockBuilder("")
        for fact in facts:
            theoriq_fact = fact.to_theoriq_fact(request_id)
            block_builder.merge(theoriq_fact.to_block_builder())
        return self._attenuate_third_party_block(agent_pk, block_builder)

    def _attenuate_third_party_block(self, agent_pk: PrivateKey, block_builder: BlockBuilder) -> TheoriqBiscuit:
        agent_kp = KeyPair.from_private_key(agent_pk)
        attenuated_biscuit = self.biscuit.append_third_party_block(agent_kp, block_builder)  # type: ignore
        return TheoriqBiscuit(attenuated_biscuit)

    def authorizer(self) -> Authorizer:
        authorizer = Authorizer()
        authorizer.add_token(self.biscuit)
        return authorizer

    def read_fact(self, fact_type: Type[T]) -> T:
        facts = self.authorizer().query(fact_type.biscuit_rule())
        if len(facts) == 0:
            raise ValueError("No facts found in current biscuit")
        try:
            return fact_type.from_fact(facts[0])
        except Exception as e:
            raise ValueError("Missing information") from e
