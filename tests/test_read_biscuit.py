import pytest

from uuid import uuid4

from main import *
from biscuit import *
from biscuit_auth import *


def test_read_request_facts():
    root_kp = KeyPair()

    subject_address = "0x12"
    expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=1)
    authority = new_authority_block(subject_address, expires_at)

    # Mock request facts
    theoriq_req = TheoriqRequest("0123456789abcdef", "0x1", "0x12")
    theoriq_budget = TheoriqBudget("10.0", "USDC", "")
    req_facts = RequestFacts(uuid4(), theoriq_req, theoriq_budget)

    request_block = req_facts.to_block()
    authority.merge(request_block)

    # This is the received biscuit
    biscuit = authority.build(root_kp.private_key)
    print(biscuit.to_base64())

    # Read facts and assert they are the same as the one expected!
    read_facts = RequestFacts.from_biscuit(biscuit)
    assert read_facts == req_facts


def test_read_response_facts():
    root_kp = KeyPair()

    subject_address = "0x12"
    expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=1)
    authority = new_authority_block(subject_address, expires_at)

    # Mock response facts
    theoriq_resp = TheoriqResponse("0123456789abcdef", "0x1")
    theoriq_cost = TheoriqCost("5.0", "USDC")
    resp_facts = ResponseFacts(uuid4(), theoriq_resp, theoriq_cost)
    response_block = resp_facts.to_block()
    authority.merge(response_block)

    # This is the received biscuit
    biscuit = authority.build(root_kp.private_key)

    # Read facts and assert they are the same as the one expected!
    read_facts = ResponseFacts.from_biscuit(biscuit)
    assert read_facts == resp_facts


def new_authority_block(subject_addr: str, expires_at: datetime) -> BiscuitBuilder:
    return BiscuitBuilder(
        """
        theoriq:subject("agent", {subject_addr});
        theoriq:expires_at({expires_at});
        """,
        {"subject_addr": subject_addr, "expires_at": int(expires_at.timestamp())},
    )

