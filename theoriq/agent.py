from __future__ import annotations

import os

import biscuit_auth
from biscuit_auth import Biscuit, KeyPair, PrivateKey, PublicKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from theoriq.biscuit import default_authorizer
from theoriq.error import AuthorizationError, ParseBiscuitError, VerificationError
from theoriq.facts import RequestFacts, TheoriqCost
from theoriq.types import AgentAddress, RequestBiscuit, ResponseBiscuit
from theoriq.utils import hash_body


class AgentConfig:
    """Expected configuration for a 'Theoriq' agent."""

    def __init__(self, theoriq_public_key: PublicKey, agent_kp: KeyPair) -> None:
        self.theoriq_public_key: PublicKey = theoriq_public_key
        self.agent_private_key: PrivateKey = agent_kp.private_key
        # TODO: Rename to AgentId
        self.agent_address = AgentAddress.from_public_key(agent_kp.public_key)

    @classmethod
    def from_env(cls) -> AgentConfig:
        theoriq_public_key = PublicKey.from_hex(os.environ["THEORIQ_PUBLIC_KEY"])
        agent_private_key = PrivateKey.from_hex(os.environ["AGENT_PRIVATE_KEY"])
        agent_kp = KeyPair.from_private_key(agent_private_key)

        return cls(theoriq_public_key, agent_kp)


class Agent:
    """
    Class holding general functionality needed for a 'Theoriq' agent.

    This class helps with the integration with biscuits and theoriq signing challenge.

    Attributes:
        config (AgentConfig): Agent configuration.
    """

    def __init__(self, config: AgentConfig) -> None:
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
        request_biscuit = RequestBiscuit(biscuit)
        self._verify_biscuit(request_biscuit, body)
        return request_biscuit

    def attenuate_biscuit_for_response(
        self, req_biscuit: RequestBiscuit, body: bytes, cost: TheoriqCost
    ) -> ResponseBiscuit:
        agent_kp = KeyPair.from_private_key(self.config.agent_private_key)
        return req_biscuit.attenuate_for_response(body, cost, agent_kp)

    def _parse_biscuit_from_base64(self, token: str) -> Biscuit:
        try:
            return Biscuit.from_base64(token, self.config.theoriq_public_key)
        except biscuit_auth.BiscuitValidationError as validation_err:
            raise ParseBiscuitError(f"fail to parse token {token[:3]}...") from validation_err

    def _verify_biscuit(self, req_biscuit: RequestBiscuit, body: bytes) -> None:
        self._authorize_biscuit(req_biscuit.biscuit)
        self._verify_biscuit_facts(req_biscuit.req_facts, body)

    def _authorize_biscuit(self, biscuit: Biscuit):
        """Authorize the given biscuit."""
        authorizer = default_authorizer(self.config.agent_address)
        authorizer.add_token(biscuit)
        try:
            authorizer.authorize()
        except biscuit_auth.AuthorizationError as auth_err:
            raise AuthorizationError(f"biscuit is not authorized. {auth_err}") from auth_err

    def _verify_biscuit_facts(self, facts: RequestFacts, body: bytes) -> None:
        if not (self._verify_target_address(facts)):
            raise VerificationError("biscuit's target address does not match our agent's address")
        if not (self._verify_request_body(facts, body)):
            raise VerificationError("biscuit's request body does not match the received body")

    def _verify_target_address(self, req_facts: RequestFacts) -> bool:
        """Verify the request facts target our agent"""
        target_address = AgentAddress(req_facts.request.to_addr)
        return target_address == self.config.agent_address

    @staticmethod
    def _verify_request_body(req_facts: RequestFacts, body: bytes) -> bool:
        """Verify that the request facts match with the given body"""
        hashed_received_body = hash_body(body)
        return hashed_received_body == req_facts.request.body_hash

    def sign_challenge(self, challenge: bytes) -> bytes:
        """Sign the given challenge with the Agent's private key"""
        private_key_bytes = bytes(self.config.agent_private_key.to_bytes())
        private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        return private_key.sign(challenge)
