from biscuit_auth import Biscuit, KeyPair

from .biscuit import attenuate_for_response
from .facts import RequestFacts, ResponseFacts, TheoriqCost, TheoriqResponse
from .response_biscuit import ResponseBiscuit


class RequestBiscuit:
    """Request biscuit used by the `theoriq` protocol"""

    def __init__(self, biscuit: Biscuit) -> None:
        self.biscuit = biscuit
        self.req_facts = RequestFacts.from_biscuit(biscuit)

    def attenuate_for_response(self, body: bytes, cost: TheoriqCost, agent_kp: KeyPair) -> ResponseBiscuit:
        theoriq_response = TheoriqResponse.from_body(body, to_addr=self.req_facts.request.from_addr)
        response_facts = ResponseFacts(self.req_facts.req_id, theoriq_response, cost)
        attenuated_biscuit = attenuate_for_response(self.biscuit, response_facts, agent_kp)

        return ResponseBiscuit(attenuated_biscuit, response_facts)
