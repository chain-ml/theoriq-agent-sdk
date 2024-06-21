from typing import Optional

import biscuit_auth
import biscuit_auth.biscuit_auth
import pytest
import theoriq.biscuit
import utils

from uuid import uuid4

from theoriq.biscuit import default_authorizer

from datetime import datetime, timezone, timedelta

from biscuit_auth import KeyPair, AuthorizationError

from theoriq.facts import RequestFacts, ResponseFacts


@pytest.fixture
def agent_biscuit(request, biscuit_facts) -> biscuit_auth.Biscuit:
    def _biscuit_builder(addr: str, exp: datetime = None) -> biscuit_auth.Biscuit:
        root_kp = KeyPair()
        authority = utils.new_authority_block(subject_addr=addr, expires_at=exp)
        authority.merge(biscuit_facts)
        return authority.build(root_kp.private_key)

    param = request.param
    return _biscuit_builder(**param) if type(param) is dict else _biscuit_builder(param)


@pytest.fixture
def biscuit_facts(request_facts, response_facts) -> biscuit_auth.BlockBuilder:
    return request_facts.to_block() if response_facts is None else response_facts.to_block()


@pytest.fixture
def request_facts(request) -> RequestFacts:
    if getattr(request, 'param', None) is None:
        return utils.new_req_facts(b"Hello World", "0x01", "0x02", 10)
    else:
        (body, from_addr, to_addr, amount) = request.param
        return utils.new_req_facts(body, from_addr, to_addr, amount)


@pytest.fixture
def response_facts(request) -> Optional[ResponseFacts]:
    if getattr(request, 'param', None) is None:
        return None
    else:
        (uuid, body, to_addr, amount) = request.param
        return utils.new_resp_facts(uuid, body, to_addr, amount)


def one_hour_ago() -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=1)


@pytest.mark.parametrize("agent_biscuit", ["0x02"], indirect=True)
def test_authorization(agent_biscuit):
    authorizer = default_authorizer("0x02")
    authorizer.add_token(agent_biscuit)
    authorizer.authorize()


@pytest.mark.parametrize("agent_biscuit", ["0x02"], indirect=True)
def test_authorization_wrong_subject_address_raises_authorization_error(agent_biscuit):
    wrong_subject_address = "0x42"
    authorizer = default_authorizer(wrong_subject_address)
    authorizer.add_token(agent_biscuit)

    with pytest.raises(AuthorizationError):
        authorizer.authorize()


@pytest.mark.parametrize("agent_biscuit", [{"addr": "0x02", "exp": one_hour_ago()}], indirect=True)
def test_authorization_expired_raises_authorization_error(agent_biscuit):
    authorizer = default_authorizer("0x01")
    authorizer.add_token(agent_biscuit)

    with pytest.raises(AuthorizationError):
        authorizer.authorize()


@pytest.mark.parametrize("request_facts", [(b"hello", "0x01", "0x02", 10.0)], indirect=True)
@pytest.mark.parametrize("agent_biscuit", ["0x02"], indirect=True)
def test_read_request_facts(request_facts, agent_biscuit):
    read_facts = RequestFacts.from_biscuit(agent_biscuit)
    assert read_facts == request_facts


@pytest.mark.parametrize("response_facts", [(uuid4(), b"hello", "0x01", 5)], indirect=True)
@pytest.mark.parametrize("agent_biscuit", ["0x01"], indirect=True)
def test_read_response_facts(agent_biscuit, response_facts):
    read_facts = ResponseFacts.from_biscuit(agent_biscuit)
    assert read_facts == response_facts


@pytest.mark.parametrize("agent_biscuit", ["0x02"], indirect=True)
def test_append_request_facts(agent_biscuit):
    # Attenuate biscuit with request facts
    agent_kp = KeyPair()
    req_facts = utils.new_req_facts(b"help", "0x02", "0x03", 5.0)
    agent_biscuit = theoriq.biscuit.attenuate_for_request(agent_biscuit, req_facts, agent_kp)

    assert agent_biscuit.block_count() == 2


@pytest.mark.parametrize("agent_biscuit", ["0x02"], indirect=True)
def test_append_response_facts(agent_biscuit):
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
