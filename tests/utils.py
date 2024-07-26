"""Utilities used in tests."""

import uuid

from datetime import datetime, timedelta, timezone
from typing import Optional

from biscuit_auth import BiscuitBuilder, Biscuit, KeyPair

from theoriq.facts import (
    TheoriqRequest,
    TheoriqBudget,
    RequestFacts,
    TheoriqResponse,
    ResponseFacts,
    TheoriqCost,
    Currency,
)
from theoriq.types import AgentAddress
from theoriq.utils import hash_body


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
    theoriq_request = TheoriqRequest(body_hash=hash_body(body), from_addr=from_addr, to_addr=str(to_addr))
    theoriq_budget = TheoriqBudget.from_amount(amount=str(amount), currency=Currency.USDC)
    return RequestFacts(uuid.uuid4(), theoriq_request, theoriq_budget)


def new_response_facts(req_id: uuid.UUID, body: bytes, to_addr: str, amount: int) -> ResponseFacts:
    """Creates a new response facts for testing purposes"""
    theoriq_response = TheoriqResponse(body_hash=hash_body(body), to_addr=to_addr)
    theoriq_cost = TheoriqCost(amount=str(amount), currency=Currency.USDC)
    return ResponseFacts(req_id, theoriq_response, theoriq_cost)


def new_request_biscuit(req_facts: RequestFacts, keypair: KeyPair) -> Biscuit:
    """Creates a new request biscuit for testing purposes"""
    agent_address = AgentAddress(req_facts.request.to_addr)
    authority = new_authority_block(agent_address)
    authority.merge(req_facts.to_block())
    return authority.build(keypair.private_key)
