"""Utilities used in tests."""

import hashlib
import uuid

from datetime import datetime, timedelta, timezone
from typing import Optional

from biscuit_auth import BiscuitBuilder

from theoriq.facts import (
    TheoriqRequest,
    TheoriqBudget,
    RequestFacts,
    TheoriqResponse,
    ResponseFacts,
    TheoriqCost,
)
from theoriq.types import AgentAddress


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


def to_agent_address(addr: str) -> AgentAddress:
    """Create an agent address filling the given addr with zeroes"""
    sanitized_address = addr.ljust(32, "0")
    return AgentAddress(sanitized_address)


def hash_body(body: bytes) -> str:
    """Hash the given bytes using sha256"""
    hasher = hashlib.sha256()
    hasher.update(body)
    return hasher.hexdigest()
