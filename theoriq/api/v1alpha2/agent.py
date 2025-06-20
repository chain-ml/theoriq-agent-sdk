from __future__ import annotations

import os
from typing import Any, Dict, Optional

import biscuit_auth
from biscuit_auth import Biscuit, KeyPair, PrivateKey  # pylint: disable=E0611
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jsonschema import SchemaError, ValidationError
from jsonschema.validators import Draft7Validator
from pydantic import BaseModel

from theoriq.biscuit import (
    AgentAddress,
    AuthorizationError,
    RequestBiscuit,
    RequestFacts,
    ResponseBiscuit,
    TheoriqCost,
    VerificationError,
)
from theoriq.biscuit.authentication_biscuit import AuthenticationBiscuit, AuthenticationFacts
from theoriq.biscuit.payload_hash import PayloadHash
from theoriq.biscuit.theoriq_biscuit import TheoriqBiscuit, TheoriqFactBase


# as from .api.v1alpha2.schemas import AgentSchemas leads to circular import
# TODO: fix
class ExecuteSchema(BaseModel):
    request: Dict[str, Any]
    response: Dict[str, Any]


class AgentSchemaError(Exception):
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
        configuration_schema (Optional[Dict[str, Any]]): Configuration schema for the agent.
        notification_schema (Optional[Dict[str, Any]]): Notification schema for the agent.
        execute_schemas (Optional[Dict[str, ExecuteSchema]]): Execute schemas for the agent.
    """

    def __init__(
        self,
        config: AgentDeploymentConfiguration,
        configuration_schema: Optional[Dict[str, Any]] = None,
        notification_schema: Optional[Dict[str, Any]] = None,
        execute_schemas: Optional[Dict[str, ExecuteSchema]] = None,
    ) -> None:
        self._config = config
        self._configuration_schema = configuration_schema
        self._notification_schema = notification_schema
        self._execute_schemas = execute_schemas
        self.virtual_address: AgentAddress = AgentAddress.null()

    @property
    def config(self) -> AgentDeploymentConfiguration:
        return self._config

    @property
    def configuration_schema(self) -> Optional[Dict[str, Any]]:
        return self._configuration_schema

    @property
    def notification_schema(self) -> Optional[Dict[str, Any]]:
        return self._notification_schema

    @property
    def execute_schemas(self) -> Optional[Dict[str, ExecuteSchema]]:
        return self._execute_schemas

    def authentication_biscuit(self) -> AuthenticationBiscuit:
        address = self.config.address if self.virtual_address.is_null else self.virtual_address
        facts = AuthenticationFacts(address, self.config.private_key)
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
        return req_biscuit.attenuate_for_response(body, cost, self.config.private_key)

    def attenuate_biscuit(self, biscuit: TheoriqBiscuit, fact: TheoriqFactBase) -> TheoriqBiscuit:
        return biscuit.attenuate_third_party_block(self.config.private_key, fact)

    def authorize_biscuit(self, biscuit: Biscuit) -> None:
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
            msg = f"biscuit's target address '{target_address}' does not match agent's address `{target_address}`"
            raise VerificationError(msg)

        hashed_body = PayloadHash(body)
        if hashed_body != facts.request.body_hash:
            msg = f"biscuit's request body hash `{facts.request.body_hash}` does not match the received body '{hashed_body}'"
            raise VerificationError(msg)

    def sign_challenge(self, challenge: bytes) -> bytes:
        """Sign the given challenge with the Agent's private key"""
        private_key_bytes = bytes(self.config.private_key.to_bytes())
        private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        return private_key.sign(challenge)

    def validate_configuration(self, values: Any) -> None:
        if self.configuration_schema is None:
            return

        validator = Draft7Validator(self.configuration_schema)
        try:
            validator.validate(values)
        except ValidationError as e:
            raise AgentSchemaError(f"ValidationError for agent configuration: {e.message}") from e

    def __str__(self) -> str:
        return f"Address: {self.config.address}, Public key: 0x{self.config.public_key.to_hex()}"

    @property
    def public_key(self) -> str:
        pk = self.config.public_key.to_hex()
        return f"0x{pk}"

    @classmethod
    def from_env(cls, env_prefix: str = "") -> Agent:
        config = AgentDeploymentConfiguration.from_env(env_prefix=env_prefix)
        return cls(config)

    @classmethod
    def validate_schemas(
        cls,
        configuration_schema: Optional[Dict[str, Any]] = None,
        notification_schema: Optional[Dict[str, Any]] = None,
        execute_schemas: Optional[Dict[str, ExecuteSchema]] = None,
    ) -> None:
        def validate_schema(schema: Optional[Dict[str, Any]], name: str) -> None:
            if schema is not None:
                try:
                    Draft7Validator.check_schema(schema)
                except SchemaError as e:
                    raise AgentSchemaError(f"SchemaError for {name}: {e.message}") from e

        validate_schema(configuration_schema, name="configuration")
        validate_schema(notification_schema, name="notification")
        if execute_schemas is not None:
            for operation, execute_schema in execute_schemas.items():
                validate_schema(execute_schema.request, name=f"execute/{operation} request")
                validate_schema(execute_schema.response, name=f"execute/{operation} response")
