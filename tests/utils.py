"""Utilities used in tests."""

import uuid

from datetime import datetime, timedelta, timezone
from typing import Optional

import pytest
from biscuit_auth import BiscuitBuilder, KeyPair
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from theoriq.facts import (
    TheoriqRequest,
    TheoriqBudget,
    RequestFacts,
    TheoriqResponse,
    ResponseFacts,
    TheoriqCost,
)
from theoriq.types import AgentAddress
from theoriq.utils import hash_body
from theoriq.agent import AgentConfig


def new_authority_block(subject_addr: AgentAddress, expires_at: Optional[datetime] = None) -> BiscuitBuilder:
    """Creates a new authority block"""
    expires_at = expires_at or datetime.now(tz=timezone.utc) + timedelta(hours=1)
    expiration_timestamp = int(expires_at.timestamp())
    return BiscuitBuilder(
        """
        theoriq:subject("agent", {subject_addr});
        theoriq:expires_at({expires_at});
        """,
        {"subject_addr": str(subject_addr), "expires_at": expiration_timestamp},
    )


def new_req_facts(body: bytes, from_addr: str, to_addr: AgentAddress, amount: int) -> RequestFacts:
    """Creates a new request facts for testing purposes"""
    theoriq_req = TheoriqRequest(hash_body(body), from_addr, str(to_addr))
    theoriq_budget = TheoriqBudget(str(amount), "USDC", "")
    return RequestFacts(uuid.uuid4(), theoriq_req, theoriq_budget)


def new_resp_facts(req_id: uuid.UUID, body: bytes, to_addr: str, amount: int) -> ResponseFacts:
    """Creates a new response facts for testing purposes"""
    theoriq_resp = TheoriqResponse(hash_body(body), to_addr)
    theoriq_cost = TheoriqCost(str(amount), "USDC")
    return ResponseFacts(req_id, theoriq_resp, theoriq_cost)


@pytest.fixture
def agent_config() -> AgentConfig:
    """
    Fixture creating an `AgentConfig` for testing purposes

    :return: AgentConfig
    """

    theoriq_public_key = KeyPair()
    agent_keypair = KeyPair()

    return AgentConfig(
        theoriq_public_key=theoriq_public_key.public_key,
        private_key=agent_keypair.private_key,
        address=AgentAddress("0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"),
    )


@pytest.fixture()
def agent_public_key(agent_config: AgentConfig) -> Ed25519PublicKey:
    agent_keypair = KeyPair.from_private_key(agent_config.agent_private_key)
    public_key_bytes = bytes(agent_keypair.public_key.to_bytes())
    return Ed25519PublicKey.from_public_bytes(public_key_bytes)
