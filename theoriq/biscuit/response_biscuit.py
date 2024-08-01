from biscuit_auth import Biscuit

from .facts import ResponseFacts


class ResponseBiscuit:
    """Response biscuit used by the `theoriq` protocol"""

    def __init__(self, biscuit: Biscuit, response_facts: ResponseFacts):
        self.biscuit = biscuit
        self.resp_facts = response_facts

    def to_base64(self) -> str:
        return self.biscuit.to_base64()
