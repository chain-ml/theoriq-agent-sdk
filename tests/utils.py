"""Utilities used in tests."""

import uuid

from biscuit_auth import Biscuit, KeyPair
from biscuit_auth.biscuit_auth import PrivateKey

from theoriq.biscuit import AgentAddress, RequestFacts, ResponseFacts, TheoriqCost
from theoriq.biscuit.facts import TheoriqBudget, TheoriqRequest, TheoriqResponse
from theoriq.types.currency import Currency
from theoriq.utils import hash_body


def new_request_facts(body: bytes, from_addr: AgentAddress, to_addr: AgentAddress, amount: int) -> RequestFacts:
    """Creates a new request facts for testing purposes"""
    theoriq_request = TheoriqRequest(body_hash=hash_body(body), from_addr=str(from_addr), to_addr=str(to_addr))
    theoriq_budget = TheoriqBudget.from_amount(amount=str(amount), currency=Currency.USDC)
    return RequestFacts(uuid.uuid4(), theoriq_request, theoriq_budget)


def new_response_facts(request_id: uuid.UUID, body: bytes, to_addr: AgentAddress, amount: int) -> ResponseFacts:
    """Creates a new response facts for testing purposes"""
    theoriq_response = TheoriqResponse.from_body(body=body, to_addr=str(to_addr))
    theoriq_cost = TheoriqCost(amount=amount, currency=Currency.USDC)
    return ResponseFacts(request_id, theoriq_response, theoriq_cost)


def new_biscuit_for_request(request_facts: RequestFacts, private_key: PrivateKey) -> Biscuit:
    """Creates a new request biscuit for testing purposes"""
    authority = AgentAddress(request_facts.request.to_addr).new_authority_builder()
    authority.merge(request_facts.to_block_builder())
    return authority.build(private_key)
