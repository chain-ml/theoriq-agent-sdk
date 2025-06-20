"""Utilities used in tests."""

import uuid

from biscuit_auth import PrivateKey

from theoriq.biscuit import AgentAddress, RequestBiscuit, RequestFacts, ResponseFacts
from theoriq.biscuit.facts import PayloadHash, TheoriqRequest, TheoriqResponse


def new_request_facts(body: bytes, from_addr: AgentAddress, to_addr: AgentAddress) -> RequestFacts:
    """Creates a new request facts for testing purposes"""
    theoriq_request = TheoriqRequest(body_hash=PayloadHash(body), from_addr=str(from_addr), to_addr=str(to_addr))
    return RequestFacts(uuid.uuid4(), theoriq_request)


def new_response_facts(request_id: uuid.UUID, body: bytes, to_addr: AgentAddress) -> ResponseFacts:
    """Creates a new response facts for testing purposes"""
    theoriq_response = TheoriqResponse.from_body(body=body, to_addr=str(to_addr))
    return ResponseFacts(request_id, theoriq_response)


def new_biscuit_for_request(request_facts: RequestFacts, private_key: PrivateKey) -> RequestBiscuit:
    """Creates a new request biscuit for testing purposes"""
    authority = AgentAddress(request_facts.request.to_addr).new_authority_builder()
    authority.merge(request_facts.to_block_builder())
    return RequestBiscuit(authority.build(private_key))
