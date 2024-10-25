from __future__ import annotations

from uuid import UUID

from biscuit_auth import Authorizer, Biscuit, BlockBuilder, Rule  # pylint: disable=E0611
from theoriq.biscuit import PayloadHash, TheoriqCost, TheoriqResponse
from theoriq.types.currency import Currency


class ResponseBiscuit:
    """Response biscuit used by the `theoriq` protocol"""

    def __init__(self, biscuit: Biscuit, response_facts: ResponseFacts):
        self.biscuit = biscuit
        self.resp_facts = response_facts

    def to_base64(self) -> str:
        return self.biscuit.to_base64()


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
        theoriq_response = TheoriqResponse(body_hash=PayloadHash.from_hash(body_hash), to_addr=to_addr)
        theoriq_cost = TheoriqCost(amount=amount, currency=Currency.from_value(currency))

        return ResponseFacts(req_id, theoriq_response, theoriq_cost)

    def to_block_builder(self) -> BlockBuilder:
        """Construct a biscuit block using the response facts"""
        block_builder = BlockBuilder("")
        block_builder.add_fact(self.response.to_fact(self.req_id))
        block_builder.add_fact(self.cost.to_fact(self.req_id))

        return block_builder
