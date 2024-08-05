from biscuit_auth import Biscuit, KeyPair

from .facts import RequestFacts, ResponseFacts, TheoriqCost, TheoriqResponse
from .response_biscuit import ResponseBiscuit


class RequestBiscuit:
    """Request biscuit used by the `theoriq` protocol"""

    def __init__(self, biscuit: Biscuit) -> None:
        self._biscuit = biscuit
        self.request_facts = RequestFacts.from_biscuit(biscuit)

    def attenuate_for_response(self, body: bytes, cost: TheoriqCost, agent_kp: KeyPair) -> ResponseBiscuit:
        theoriq_response = TheoriqResponse.from_body(body, to_addr=self.request_facts.request.from_addr)
        response_facts = ResponseFacts(self.request_facts.req_id, theoriq_response, cost)
        attenuated_biscuit = self._biscuit.append_third_party_block(agent_kp, response_facts.to_block_builder())  # type: ignore

        return ResponseBiscuit(attenuated_biscuit, response_facts)
