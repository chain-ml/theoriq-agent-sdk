from __future__ import annotations

import os
from typing import Dict, Optional

import biscuit_auth
from biscuit_auth import Biscuit, KeyPair, PrivateKey  # pylint: disable=E0611
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jsonschema.validators import Draft7Validator

from .biscuit import (
    AgentAddress,
    AuthorizationError,
    RequestBiscuit,
    RequestFacts,
    ResponseBiscuit,
    TheoriqCost,
    VerificationError,
)
from .utils import hash_body


class AgentConfig:
    """Expected configuration for a 'Theoriq' agent."""

    def __init__(self, private_key: PrivateKey) -> None:
        agent_kp = KeyPair.from_private_key(private_key)
        self.private_key: PrivateKey = private_key
        self.address = AgentAddress.from_public_key(agent_kp.public_key)
        self.public_key = agent_kp.public_key

    @classmethod
    def from_env(cls) -> AgentConfig:
        private_key = os.environ["AGENT_PRIVATE_KEY"]
        agent_private_key = PrivateKey.from_hex(private_key.removeprefix("0x"))
        return cls(agent_private_key)

    def __str__(self):
        return f"Address: {self.address}, Public key:{self.public_key.to_hex()}"


class Agent:
    """
    Class holding general functionality needed for a 'Theoriq' agent.

    This class helps with the integration with biscuits and theoriq signing challenge.

    Attributes:
        config (AgentConfig): Agent configuration.
        schema (Optional[Dict]): Configuration Schema for the agent.
    """

    def __init__(self, config: AgentConfig, schema: Optional[Dict] = None) -> None:
        self._config = config
        self._schema = schema

    @property
    def config(self) -> AgentConfig:
        return self._config

    @property
    def schema(self) -> Optional[Dict]:
        return self._schema

    def verify_biscuit(self, request_biscuit: RequestBiscuit, body: bytes) -> None:
        """
        Verify the biscuit.

        :param body: the body of the request
        :raises ParseBiscuitError: if the biscuit could not be parsed.
        :raises VerificationError: if the biscuit is not valid.
        """
        self._authorize_biscuit(request_biscuit.biscuit)
        self._verify_biscuit_facts(request_biscuit.request_facts, body)

    def attenuate_biscuit_for_response(
        self, req_biscuit: RequestBiscuit, body: bytes, cost: TheoriqCost
    ) -> ResponseBiscuit:
        return req_biscuit.attenuate_for_response(body, cost, self.config.private_key)

    def _authorize_biscuit(self, biscuit: Biscuit):
        """Runs the authorization checks and policies on the given biscuit."""
        authorizer = self.config.address.default_authorizer()
        authorizer.add_token(biscuit)
        try:
            authorizer.authorize()
        except biscuit_auth.AuthorizationError as auth_err:
            raise AuthorizationError(f"biscuit is not authorized. {auth_err}") from auth_err

    def _verify_biscuit_facts(self, facts: RequestFacts, body: bytes) -> None:
        """Verify Facts on the given biscuit."""
        target_address = AgentAddress(facts.request.to_addr)
        if target_address != self.config.address:
            raise VerificationError(f"biscuit's target address '{target_address}' does not match our agent's address")
        hashed_body = hash_body(body)
        if hashed_body != facts.request.body_hash:
            raise VerificationError(f"biscuit's request body hash does not match the received body '{hashed_body}'")

    def sign_challenge(self, challenge: bytes) -> bytes:
        """Sign the given challenge with the Agent's private key"""
        private_key_bytes = bytes(self.config.private_key.to_bytes())
        private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        return private_key.sign(challenge)

    @property
    def public_key(self) -> str:
        pk = self.config.public_key.to_hex()
        return f"0x{pk}"

    @classmethod
    def from_env(cls) -> Agent:
        config = AgentConfig.from_env()
        return cls(config)

    @classmethod
    def validate_schema(cls, schema: Optional[Dict]):
        if schema is not None:
            Draft7Validator.check_schema(schema)
