from __future__ import annotations

import uuid
from uuid import UUID

from biscuit_auth import Authorizer, Biscuit, BlockBuilder, KeyPair, Rule  # pylint: disable=E0611

from ..types.currency import Currency
from . import ResponseFacts, TheoriqBudget
from .facts import TheoriqCost, TheoriqRequest, TheoriqResponse
from .response_biscuit import ResponseBiscuit


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


class RequestBiscuit:
    """Request biscuit used by the `theoriq` protocol"""

    def __init__(self, biscuit: Biscuit) -> None:
        self.biscuit = biscuit
        self.request_facts = RequestFacts.from_biscuit(biscuit)

    def attenuate_for_response(self, body: bytes, cost: TheoriqCost, agent_kp: KeyPair) -> ResponseBiscuit:
        theoriq_response = TheoriqResponse.from_body(body, to_addr=self.request_facts.request.from_addr)
        response_facts = ResponseFacts(self.request_facts.req_id, theoriq_response, cost)
        attenuated_biscuit = self.biscuit.append_third_party_block(agent_kp, response_facts.to_block_builder())  # type: ignore

        return ResponseBiscuit(attenuated_biscuit, response_facts)
