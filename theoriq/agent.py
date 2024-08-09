from __future__ import annotations

import os

import biscuit_auth
from biscuit_auth import Biscuit, KeyPair, PrivateKey, PublicKey  # pylint: disable=E0611
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .biscuit import (
    AgentAddress,
    AuthorizationError,
    RequestBiscuit,
    RequestFacts,
    ResponseBiscuit,
    TheoriqCost,
    VerificationError,
    from_base64_token,
)
from .utils import hash_body


class AgentConfig:
    """Expected configuration for a 'Theoriq' agent."""

    def __init__(self, theoriq_public_key: PublicKey, agent_kp: KeyPair) -> None:
        self.theoriq_public_key: PublicKey = theoriq_public_key
        self.agent_private_key: PrivateKey = agent_kp.private_key
        self.agent_address = AgentAddress.from_public_key(agent_kp.public_key)
        self.agent_public_key = agent_kp.public_key

    @classmethod
    def from_env(cls) -> AgentConfig:
        theoriq_public_key = PublicKey.from_hex(os.environ["THEORIQ_PUBLIC_KEY"])
        agent_private_key = PrivateKey.from_hex(os.environ["AGENT_PRIVATE_KEY"])
        agent_kp = KeyPair.from_private_key(agent_private_key)

        return cls(theoriq_public_key, agent_kp)

    def __str__(self):
        return f"Address: {self.agent_address}, Public key:{self.agent_public_key.to_hex()}"


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
        biscuit = from_base64_token(token, self.config.theoriq_public_key)
        request_biscuit = RequestBiscuit(biscuit)
        self._verify_request_biscuit(request_biscuit, body)
        return request_biscuit

    def attenuate_biscuit_for_response(
        self, req_biscuit: RequestBiscuit, body: bytes, cost: TheoriqCost
    ) -> ResponseBiscuit:
        agent_kp = KeyPair.from_private_key(self.config.agent_private_key)
        return req_biscuit.attenuate_for_response(body, cost, agent_kp)

    def _verify_request_biscuit(self, req_biscuit: RequestBiscuit, body: bytes) -> None:
        self._authorize_biscuit(req_biscuit.biscuit)
        self._verify_biscuit_facts(req_biscuit.request_facts, body)

    def _authorize_biscuit(self, biscuit: Biscuit):
        """Runs the authorization checks and policies on the given biscuit."""
        authorizer = self.config.agent_address.default_authorizer()
        authorizer.add_token(biscuit)
        try:
            authorizer.authorize()
        except biscuit_auth.AuthorizationError as auth_err:
            raise AuthorizationError(f"biscuit is not authorized. {auth_err}") from auth_err

    def _verify_biscuit_facts(self, facts: RequestFacts, body: bytes) -> None:
        """Verify Facts on the given biscuit."""
        target_address = AgentAddress(facts.request.to_addr)
        if target_address != self.config.agent_address:
            raise VerificationError(f"biscuit's target address '{target_address}' does not match our agent's address")
        hashed_body = hash_body(body)
        if hashed_body != facts.request.body_hash:
            raise VerificationError(f"biscuit's request body hash does not match the received body '{hashed_body}'")

    def sign_challenge(self, challenge: bytes) -> bytes:
        """Sign the given challenge with the Agent's private key"""
        private_key_bytes = bytes(self.config.agent_private_key.to_bytes())
        private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        return private_key.sign(challenge)

    @property
    def public_key(self) -> str:
        return self.config.agent_public_key.to_hex()

    @classmethod
    def from_env(cls) -> Agent:
        config = AgentConfig.from_env()
        return cls(config)
