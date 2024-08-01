"""Utilities used in tests."""

import uuid

from biscuit_auth import Biscuit, KeyPair
from theoriq.biscuit import RequestFacts, ResponseFacts, TheoriqCost, new_authority_block
from theoriq.biscuit.facts import TheoriqBudget, TheoriqRequest, TheoriqResponse
from theoriq.types import AgentAddress
from theoriq.types.currency import Currency
from theoriq.utils import hash_body


def new_req_facts(body: bytes, from_addr: str, to_addr: AgentAddress, amount: int) -> RequestFacts:
    """Creates a new request facts for testing purposes"""
    theoriq_request = TheoriqRequest(body_hash=hash_body(body), from_addr=from_addr, to_addr=str(to_addr))
    theoriq_budget = TheoriqBudget.from_amount(amount=str(amount), currency=Currency.USDC)
    return RequestFacts(uuid.uuid4(), theoriq_request, theoriq_budget)


def new_response_facts(req_id: uuid.UUID, body: bytes, to_addr: str, amount: int) -> ResponseFacts:
    """Creates a new response facts for testing purposes"""
    theoriq_response = TheoriqResponse.from_body(body=body, to_addr=to_addr)
    theoriq_cost = TheoriqCost(amount=amount, currency=Currency.USDC)
    return ResponseFacts(req_id, theoriq_response, theoriq_cost)


def new_request_biscuit(req_facts: RequestFacts, keypair: KeyPair) -> Biscuit:
    """Creates a new request biscuit for testing purposes"""
    authority = new_authority_block(req_facts.request.to_addr)
    authority.merge(req_facts.to_block_builder())
    return authority.build(keypair.private_key)
