from __future__ import annotations

import os
import uuid
from typing import Any, Dict
from uuid import UUID

from biscuit_auth import Authorizer, Biscuit, BlockBuilder, KeyPair, Rule  # pylint: disable=E0611
from biscuit_auth.biscuit_auth import PrivateKey, PublicKey  # type: ignore

from ..types.currency import Currency
from . import AgentAddress
from .facts import TheoriqBudget, TheoriqCost, TheoriqRequest, TheoriqResponse
from .response_biscuit import ResponseBiscuit, ResponseFacts
from .utils import from_base64_token


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

    @staticmethod
    def generate_new_biscuit(body: bytes, *, from_addr: str, to_addr: str) -> Biscuit:
        subject_address = AgentAddress(to_addr)
        request_facts = RequestFacts.default(body=body, from_addr=from_addr, to_addr=to_addr)

        tq_private_key = os.getenv("THEORIQ_PRIVATE_KEY", "")
        private_key = PrivateKey.from_hex(tq_private_key.removeprefix("0x"))

        authority_block_builder = subject_address.new_authority_builder()
        authority_block_builder.merge(request_facts.to_block_builder())
        return authority_block_builder.build(private_key)

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


class RequestBiscuit:
    """Request biscuit used by the `Theoriq` protocol"""

    def __init__(self, biscuit: Biscuit) -> None:
        self.biscuit: Biscuit = biscuit
        self.request_facts = RequestFacts.from_biscuit(biscuit)

    def attenuate_for_response(self, body: bytes, cost: TheoriqCost, agent_private_key: PrivateKey) -> ResponseBiscuit:
        theoriq_response = TheoriqResponse.from_body(body, to_addr=self.request_facts.request.from_addr)
        response_facts = ResponseFacts(self.request_facts.req_id, theoriq_response, cost)
        agent_kp = KeyPair.from_private_key(agent_private_key)
        attenuated_biscuit = self.biscuit.append_third_party_block(agent_kp, response_facts.to_block_builder())  # type: ignore

        return ResponseBiscuit(attenuated_biscuit, response_facts)

    def attenuate_for_request(
        self, request: TheoriqRequest, budget: TheoriqBudget, agent_private_key: PrivateKey
    ) -> RequestBiscuit:
        agent_kp = KeyPair.from_private_key(agent_private_key)
        request_facts = RequestFacts(uuid.uuid4(), request, budget)
        attenuated_biscuit = self.biscuit.append_third_party_block(agent_kp, request_facts.to_block_builder())  # type: ignore
        return RequestBiscuit(attenuated_biscuit)

    def to_base64(self) -> str:
        return self.biscuit.to_base64()

    def to_headers(self) -> Dict[str, Any]:
        return {
            "Content-Type": "application/json",
            "Authorization": "bearer " + self.biscuit.to_base64(),
        }

    def __str__(self):
        return f"RequestBiscuit(biscuit={self.biscuit}, request_facts={self.request_facts})"

    @classmethod
    def from_token(cls, *, token: str, public_key: str) -> RequestBiscuit:
        public_key = public_key.removeprefix("0x")
        biscuit = from_base64_token(token, PublicKey.from_hex(public_key))
        return cls(biscuit)
