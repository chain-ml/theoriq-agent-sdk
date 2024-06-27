import hashlib
import os

import biscuit_auth
from biscuit_auth import PublicKey, PrivateKey, Biscuit, KeyPair

from theoriq.error import VerificationError, ParseBiscuitError
from theoriq.facts import RequestFacts, TheoriqCost
from theoriq.types import AgentAddress, RequestBiscuit, ResponseBiscuit
from theoriq.biscuit import default_authorizer


class AgentConfig:
    """Expected configuration for a `theoriq` agent."""

    def __init__(self, theoriq_public_key: PublicKey, private_key: PrivateKey, address: AgentAddress):
        self.theoriq_public_key = theoriq_public_key
        self.agent_private_key = private_key
        self.agent_address = address

    @classmethod
    def from_env(cls) -> "AgentConfig":
        theoriq_public_key = PublicKey.from_hex(os.environ["THEORIQ_PUBLIC_KEY"])
        agent_private_key = PrivateKey.from_hex(os.environ["AGENT_PRIVATE_KEY"])
        agent_address = AgentAddress(os.environ["AGENT_ADDRESS"])

        return cls(theoriq_public_key, agent_private_key, agent_address)


class Agent:
    """Class used to interact with the biscuits"""

    def __init__(self, config: AgentConfig):
        self.config = config

    def parse_and_verify_biscuit(self, token: str, body: bytes) -> RequestBiscuit:
        """
        Parse the biscuit from the given token and verify it.

        :param token: the biscuit base64 encoded
        :param body: the body of the request
        :raises ParseBiscuitError: if the biscuit could not be parsed.
        :raises VerificationError: if the biscuit is not valid.
        """
        biscuit = self._parse_biscuit_from_base64(token)
        req_biscuit = RequestBiscuit(biscuit)
        self._verify_biscuit(req_biscuit, body)
        return req_biscuit

    def attenuate_biscuit_for_response(
        self, req_biscuit: RequestBiscuit, body: bytes, cost: TheoriqCost
    ) -> ResponseBiscuit:
        agent_kp = KeyPair.from_private_key(self.config.agent_private_key)
        return req_biscuit.attenuate_for_response(body, cost, agent_kp)

    def _parse_biscuit_from_base64(self, token: str) -> Biscuit:
        try:
            return Biscuit.from_base64(token, self.config.theoriq_public_key)
        except biscuit_auth.BiscuitValidationError as validation_err:
            raise ParseBiscuitError(validation_err)

    def _verify_biscuit(self, req_biscuit: RequestBiscuit, body: bytes):
        self._authorize_biscuit(req_biscuit)
        self._verify_biscuit_facts(req_biscuit, body)

    def _authorize_biscuit(self, req_biscuit: RequestBiscuit):
        """Authorize the given biscuit."""
        authorizer = default_authorizer(self.config.agent_address)
        authorizer.add_token(req_biscuit.biscuit)
        authorizer.authorize()

    def _verify_biscuit_facts(self, req_biscuit: RequestBiscuit, body: bytes):
        req_facts = req_biscuit.req_facts
        if not (self._verify_target_address(req_facts)):
            raise VerificationError("biscuit's target address does not match our agent's address")
        if not (self._verify_request_body(req_facts, body)):
            raise VerificationError("biscuit's request body does not match the received body")

    def _verify_target_address(self, req_facts: RequestFacts) -> bool:
        """Verify the request facts target our agent"""
        target_address = AgentAddress(req_facts.request.to_addr)
        return target_address == self.config.agent_address

    @staticmethod
    def _verify_request_body(req_facts: RequestFacts, body: bytes) -> bool:
        """Verify that the request facts match with the given body"""
        hashed_received_body = Agent._hash_body(body)
        return hashed_received_body == req_facts.request.body_hash

    @staticmethod
    def _hash_body(body: bytes) -> bytes:
        """Hash the given body using the sha256 algorithm."""
        return hashlib.sha256(body).digest()
