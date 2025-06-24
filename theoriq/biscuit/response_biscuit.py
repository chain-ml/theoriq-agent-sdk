from __future__ import annotations

from uuid import UUID

from biscuit_auth import Biscuit, BlockBuilder  # pylint: disable=E0611

from .facts import ExecuteResponseFacts, TheoriqResponse
from .theoriq_biscuit import TheoriqBiscuit


class ResponseBiscuit:
    """Response biscuit used by the `theoriq` protocol"""

    def __init__(self, biscuit: Biscuit, response_facts: ResponseFacts):
        self.biscuit = biscuit
        self.resp_facts = response_facts

    def to_base64(self) -> str:
        return self.biscuit.to_base64()


class ResponseFacts:
    """Required facts inside the response biscuit"""

    def __init__(self, request_id: UUID | str, response: TheoriqResponse):
        self.req_id = request_id if isinstance(request_id, UUID) else UUID(request_id)
        self.response = response

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def __str__(self) -> str:
        return f"req_id={self.req_id}, response={self.response}"

    @staticmethod
    def from_biscuit(biscuit: Biscuit) -> ResponseFacts:
        """Read response facts from biscuit"""
        theoriq_biscuit = TheoriqBiscuit(biscuit)
        biscuit_facts = theoriq_biscuit.read_fact(ExecuteResponseFacts)
        request_id = biscuit_facts.response.request_id
        theoriq_response = TheoriqResponse.from_theoriq_fact(biscuit_facts.response)
        return ResponseFacts(request_id, theoriq_response)

    def to_block_builder(self) -> BlockBuilder:
        """Construct a biscuit block using the response facts"""
        response_fact = self.response.to_theoriq_fact(self.req_id)

        block_builder = BlockBuilder("")
        block_builder.merge(response_fact.to_block_builder())
        return block_builder
