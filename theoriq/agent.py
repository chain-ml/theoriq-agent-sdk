from __future__ import annotations

import os
from typing import Any, Dict, Optional

import biscuit_auth
from biscuit_auth import Biscuit, KeyPair, PrivateKey  # pylint: disable=E0611
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jsonschema import ValidationError
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
from .biscuit.authentication_biscuit import AuthenticationBiscuit, AuthenticationFacts
from .biscuit.payload_hash import PayloadHash
from .biscuit.theoriq_biscuit import TheoriqBiscuit, TheoriqFactBase


class AgentConfigurationSchemaError(Exception):
    pass


class AgentDeploymentConfiguration:
    """Expected configuration for a deployment of a 'Theoriq' agent."""

    def __init__(self, private_key: PrivateKey, prefix: str = "") -> None:
        agent_kp = KeyPair.from_private_key(private_key)
        self.private_key: PrivateKey = private_key
        self.address = AgentAddress.from_public_key(agent_kp.public_key)
        self.public_key = agent_kp.public_key
        self.prefix = prefix

    @classmethod
    def from_env(cls, env_prefix: str = "") -> AgentDeploymentConfiguration:
        private_key = os.environ[f"{env_prefix}AGENT_PRIVATE_KEY"]
        agent_private_key = PrivateKey.from_hex(private_key.removeprefix("0x"))
        return cls(agent_private_key, prefix=env_prefix)

    @property
    def agent_yaml_path(self) -> Optional[str]:
        return os.getenv(f"{self.prefix}AGENT_YAML_PATH")

    def __str__(self) -> str:
        return f"Address: {self.address}, Public key:0x{self.public_key.to_hex()}"


class Agent:
    """
    Class holding general functionality needed for a 'Theoriq' agent.

    This class helps with the integration with biscuits and theoriq signing challenge.

    Attributes:
        config (AgentDeploymentConfiguration): Agent configuration.
        schema (Optional[Dict]): Configuration Schema for the agent.
    """

    def __init__(self, config: AgentDeploymentConfiguration, schema: Optional[Dict] = None) -> None:
        self._config = config
        self._schema = schema
        self.virtual_address: AgentAddress = AgentAddress.null()

    @property
    def config(self) -> AgentDeploymentConfiguration:
        return self._config

    @property
    def schema(self) -> Optional[Dict]:
        return self._schema

    def authentication_biscuit(self) -> AuthenticationBiscuit:
        address = self._config.address if self.virtual_address.is_null else self.virtual_address
        facts = AuthenticationFacts(address, self._config.private_key)
        return facts.to_authentication_biscuit()

    def verify_biscuit(self, request_biscuit: RequestBiscuit, body: bytes) -> None:
        """
        Verify the biscuit.

        :param request_biscuit: Request biscuit.
        :param body: the body of the request
        :raises ParseBiscuitError: if the biscuit could not be parsed.
        :raises VerificationError: if the biscuit is not valid.
        """
        self.authorize_biscuit(request_biscuit.biscuit)
        self._verify_biscuit_facts(request_biscuit.request_facts, body)

    def attenuate_biscuit_for_response(
        self, req_biscuit: RequestBiscuit, body: bytes, cost: TheoriqCost
    ) -> ResponseBiscuit:
        return req_biscuit.attenuate_for_response(body, cost, self._config.private_key)

    def attenuate_biscuit(self, biscuit: TheoriqBiscuit, fact: TheoriqFactBase) -> TheoriqBiscuit:
        return biscuit.attenuate_third_party_block(self._config.private_key, fact)

    def authorize_biscuit(self, biscuit: Biscuit):
        """Runs the authorization checks and policies on the given biscuit."""
        authorizer = self._config.address.default_authorizer()
        authorizer.add_token(biscuit)
        try:
            authorizer.authorize()
        except biscuit_auth.AuthorizationError as auth_err:
            raise AuthorizationError(f"biscuit is not authorized. {auth_err}") from auth_err

    def _verify_biscuit_facts(self, facts: RequestFacts, body: bytes) -> None:
        """Verify Facts on the given biscuit."""
        target_address = AgentAddress(facts.request.to_addr)
        if target_address != self._config.address:
            msg = f"biscuit's target address '{target_address}' does not match agent's address `{target_address}`"
            raise VerificationError(msg)

        hashed_body = PayloadHash(body)
        if hashed_body != facts.request.body_hash:
            msg = f"biscuit's request body hash `{facts.request.body_hash}` does not match the received body '{hashed_body}'"
            raise VerificationError(msg)

    def sign_challenge(self, challenge: bytes) -> bytes:
        """Sign the given challenge with the Agent's private key"""
        private_key_bytes = bytes(self._config.private_key.to_bytes())
        private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        return private_key.sign(challenge)

    def validate_configuration(self, values: Any) -> None:
        """
        Validate the configuration values against the agent's JSON schema.

        Args:
            values (Any): The configuration values to validate

        Raises:
            AgentConfigurationSchemaError: If the configuration values do not match the schema
        """
        if self.schema is None:
            return

        validator = Draft7Validator(self.schema)
        try:
            validator.validate(values)
        except ValidationError as e:
            raise AgentConfigurationSchemaError(e.message) from e

    def __str__(self) -> str:
        return f"Address: {self._config.address}, Public key: 0x{self._config.public_key.to_hex()}"

    @property
    def public_key(self) -> str:
        """
        Get the public key of the agent.

        Returns:
            str: The public key of the agent
        """
        pk = self._config.public_key.to_hex()
        return f"0x{pk}"

    @classmethod
    def from_env(cls) -> Agent:
        """
        Create an Agent instance from environment variables.

        Returns:
            Agent: An Agent instance configured from environment variables
        """
        config = AgentDeploymentConfiguration.from_env()
        return cls(config)

    @classmethod
    def validate_schema(cls, schema: Optional[Dict]) -> None:
        """
        Validate the schema against the JSON schema draft 7.

        Args:
            schema (Optional[Dict]): The schema to validate
        """
        if schema is not None:
            Draft7Validator.check_schema(schema)
