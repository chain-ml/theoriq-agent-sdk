from __future__ import annotations

from uuid import UUID

from biscuit_auth import Biscuit, BlockBuilder  # pylint: disable=E0611

from theoriq.biscuit import TheoriqBiscuit, TheoriqCost, TheoriqResponse
from theoriq.biscuit.facts import ExecuteResponseFacts


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

    def __str__(self) -> str:
        return f"req_id={self.req_id}, response={self.response}, cost={self.cost}"

    @staticmethod
    def from_biscuit(biscuit: Biscuit) -> ResponseFacts:
        """Read response facts from biscuit"""
        theoriq_biscuit = TheoriqBiscuit(biscuit)
        biscuit_facts = theoriq_biscuit.read_fact(ExecuteResponseFacts)
        request_id = biscuit_facts.response.request_id
        theoriq_response = TheoriqResponse.from_theoriq_fact(biscuit_facts.response)
        theoriq_cost = TheoriqCost.from_theoriq_fact(biscuit_facts.cost)
        return ResponseFacts(request_id, theoriq_response, theoriq_cost)

    def to_block_builder(self) -> BlockBuilder:
        """Construct a biscuit block using the response facts"""
        response_fact = self.response.to_theoriq_fact(self.req_id)
        cost_fact = self.cost.to_theoriq_fact(self.req_id)

        block_builder = BlockBuilder("")
        block_builder.merge(response_fact.to_block_builder())
        block_builder.merge(cost_fact.to_block_builder())
        return block_builder
