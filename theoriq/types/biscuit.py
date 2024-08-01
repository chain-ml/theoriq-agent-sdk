import theoriq.biscuit
from biscuit_auth import Biscuit, KeyPair
from theoriq.facts import RequestFacts, ResponseFacts, TheoriqCost, TheoriqResponse


class ResponseBiscuit:
    """Response biscuit used by the `theoriq` protocol"""

    def __init__(self, biscuit: Biscuit, response_facts: ResponseFacts):
        self.biscuit = biscuit
        self.resp_facts = response_facts

    def to_base64(self) -> str:
        return self.biscuit.to_base64()


class RequestBiscuit:
    """Request biscuit used by the `theoriq` protocol"""

    def __init__(self, biscuit: Biscuit) -> None:
        self.biscuit = biscuit
        self.req_facts = RequestFacts.from_biscuit(biscuit)

    def attenuate_for_response(self, body: bytes, cost: TheoriqCost, agent_kp: KeyPair) -> ResponseBiscuit:
        theoriq_response = TheoriqResponse.from_body(body, to_addr=self.req_facts.request.from_addr)
        response_facts = ResponseFacts(self.req_facts.req_id, theoriq_response, cost)
        attenuated_biscuit = theoriq.biscuit.attenuate_for_response(self.biscuit, response_facts, agent_kp)

        return ResponseBiscuit(attenuated_biscuit, response_facts)
