import uuid
import pytest
import theoriq.biscuit
import utils

from theoriq.biscuit import default_authorizer

from datetime import datetime, timezone, timedelta

from biscuit_auth import KeyPair, AuthorizationError

from theoriq.facts import RequestFacts, ResponseFacts


def test_authorization():
    root_kp = KeyPair()

    subject_address = "0x1234"
    authority = utils.new_authority_block(subject_address)
    biscuit = authority.build(root_kp.private_key)

    authorizer = default_authorizer(subject_address)
    authorizer.add_token(biscuit)
    authorizer.authorize()


def test_authorization_wrong_subject_address_raises_authorization_error():
    root_kp = KeyPair()

    subject_address = "0x1234"
    authority = utils.new_authority_block(subject_address)
    biscuit = authority.build(root_kp.private_key)

    authorizer = default_authorizer("0x12345")
    authorizer.add_token(biscuit)

    with pytest.raises(AuthorizationError):
        authorizer.authorize()


def test_authorization_expired_raises_authorization_error():
    root_kp = KeyPair()

    subject_address = "0x1234"
    expires_at = datetime.now(tz=timezone.utc) - timedelta(hours=1)
    authority = utils.new_authority_block(subject_address, expires_at)
    biscuit = authority.build(root_kp.private_key)

    authorizer = default_authorizer(subject_address)
    authorizer.add_token(biscuit)

    with pytest.raises(AuthorizationError):
        authorizer.authorize()


def test_read_request_facts():
    root_kp = KeyPair()

    # Build biscuit
    authority = utils.new_authority_block("0x01")
    req_facts = utils.new_req_facts(b"hello", "0x01", "0x02", 10.0)
    req_block = req_facts.to_block()
    authority.merge(req_block)
    biscuit = authority.build(root_kp.private_key)

    # Read facts and make assertions
    read_facts = RequestFacts.from_biscuit(biscuit)
    assert read_facts == req_facts


def test_read_response_facts():
    root_kp = KeyPair()

    # Build biscuit
    authority = utils.new_authority_block("0x01")
    resp_facts = utils.new_resp_facts(uuid.uuid4(), b"hello", "0x01", 10.0)
    resp_block = resp_facts.to_block()
    authority.merge(resp_block)
    biscuit = authority.build(root_kp.private_key)

    # Read facts and make assertions
    read_facts = ResponseFacts.from_biscuit(biscuit)
    assert read_facts == resp_facts


def test_append_request_facts():
    root_kp = KeyPair()
    authority = utils.new_authority_block("0x01")
    req_facts = utils.new_req_facts(b"hello", "0x01", "0x02", 10.0)
    authority.merge(req_facts.to_block())
    biscuit = authority.build(root_kp.private_key)

    # Attenuate biscuit with request facts
    agent_kp = KeyPair()
    req_facts = utils.new_req_facts(b"help", "0x02", "0x03", 5.0)
    agent_biscuit = theoriq.biscuit.attenuate_for_request(biscuit, req_facts, agent_kp)

    assert agent_biscuit.block_count() == 2


def test_append_response_facts():
    root_kp = KeyPair()
    authority = utils.new_authority_block("0x01")
    req_facts = utils.new_req_facts(b"hello", "0x01", "0x02", 10.0)
    authority.merge(req_facts.to_block())
    biscuit = authority.build(root_kp.private_key)

    # Attenuate biscuit with response facts
    agent_kp = KeyPair()
    resp_facts = utils.new_resp_facts(req_facts.req_id, b"hi", "0x01", 2.0)
    agent_biscuit = theoriq.biscuit.attenuate_for_response(
        biscuit, resp_facts, agent_kp
    )

    assert agent_biscuit.block_count() == 2
