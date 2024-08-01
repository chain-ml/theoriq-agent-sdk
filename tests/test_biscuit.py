from datetime import datetime, timedelta, timezone
from typing import Final, Optional
from uuid import uuid4

import biscuit_auth
import pytest
from biscuit_auth import AuthorizationError, KeyPair
from tests import utils
from theoriq.biscuit import attenuate_for_request, attenuate_for_response, default_authorizer, new_authority_block
from theoriq.facts import RequestFacts, ResponseFacts
from theoriq.types import AgentAddress

ADDRESS_ONE: Final[str] = "0000000000000000000000000000000000000000000000000000000000000001"
ADDRESS_TWO: Final[str] = "0000000000000000000000000000000000000000000000000000000000000002"
ADDRESS_THREE: Final[str] = "0000000000000000000000000000000000000000000000000000000000000003"


@pytest.fixture
def agent_biscuit(request, biscuit_facts) -> biscuit_auth.Biscuit:
    def _biscuit_builder(subject_addr: str, exp: Optional[datetime] = None) -> biscuit_auth.Biscuit:
        root_kp = KeyPair()
        expires_at = exp or datetime.now(tz=timezone.utc) + timedelta(hours=1)
        authority = new_authority_block(subject_addr=subject_addr, expires_at=expires_at)
        authority.merge(biscuit_facts)
        return authority.build(root_kp.private_key)

    param = request.param
    return _biscuit_builder(**param) if isinstance(param, dict) else _biscuit_builder(param)


@pytest.fixture
def biscuit_facts(request_facts, response_facts) -> biscuit_auth.BlockBuilder:
    return request_facts.to_block_builder() if response_facts is None else response_facts.to_block_builder()


@pytest.fixture
def request_facts(request) -> RequestFacts:
    if getattr(request, "param", None) is None:
        default_from_address = ADDRESS_ONE
        default_agent_address = AgentAddress(ADDRESS_TWO)
        return utils.new_req_facts(b"Hello World", default_from_address, default_agent_address, 10)
    else:
        (body, from_addr, to_addr, amount) = request.param
        return utils.new_req_facts(body, from_addr, to_addr, amount)


@pytest.fixture
def response_facts(request) -> Optional[ResponseFacts]:
    if getattr(request, "param", None) is None:
        return None
    else:
        (uuid, body, to_addr, amount) = request.param
        return utils.new_response_facts(uuid, body, to_addr, amount)


def one_hour_ago() -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=1)


@pytest.mark.parametrize("agent_biscuit", [ADDRESS_TWO], indirect=True)
def test_authorization(agent_biscuit):
    authorizer = default_authorizer(AgentAddress(ADDRESS_TWO))
    authorizer.add_token(agent_biscuit)
    authorizer.authorize()


@pytest.mark.parametrize("agent_biscuit", [ADDRESS_TWO], indirect=True)
def test_authorization_wrong_subject_address_raises_authorization_error(agent_biscuit):
    wrong_subject_address = AgentAddress("0000000000000000000000000000000000000000000000000000000000000042")
    authorizer = default_authorizer(wrong_subject_address)
    authorizer.add_token(agent_biscuit)

    with pytest.raises(AuthorizationError):
        authorizer.authorize()


@pytest.mark.parametrize("agent_biscuit", [{"subject_addr": ADDRESS_TWO, "exp": one_hour_ago()}], indirect=True)
def test_authorization_expired_raises_authorization_error(agent_biscuit):
    authorizer = default_authorizer(AgentAddress(ADDRESS_TWO))
    authorizer.add_token(agent_biscuit)

    with pytest.raises(AuthorizationError):
        authorizer.authorize()


@pytest.mark.parametrize(
    "request_facts",
    [
        (
            b"hello",
            ADDRESS_ONE,
            ADDRESS_TWO,
            10,
        )
    ],
    indirect=True,
)
@pytest.mark.parametrize("agent_biscuit", [ADDRESS_TWO], indirect=True)
def test_read_request_facts(request_facts, agent_biscuit):
    read_facts = RequestFacts.from_biscuit(agent_biscuit)
    assert read_facts == request_facts


@pytest.mark.parametrize("response_facts", [(uuid4(), b"hello", ADDRESS_ONE, 5)], indirect=True)
@pytest.mark.parametrize("agent_biscuit", [ADDRESS_ONE], indirect=True)
def test_read_response_facts(agent_biscuit, response_facts):
    read_facts = ResponseFacts.from_biscuit(agent_biscuit)
    assert read_facts == response_facts


@pytest.mark.parametrize("agent_biscuit", [ADDRESS_TWO], indirect=True)
def test_append_request_facts(agent_biscuit):
    agent_kp = KeyPair()
    target_address = AgentAddress(ADDRESS_THREE)
    req_facts = utils.new_req_facts(b"help", ADDRESS_TWO, target_address, 5)
    agent_biscuit = attenuate_for_request(agent_biscuit, req_facts, agent_kp)

    assert agent_biscuit.block_count() == 2


@pytest.mark.parametrize(
    "request_facts",
    [
        (
            b"hello",
            ADDRESS_ONE,
            ADDRESS_TWO,
            10,
        )
    ],
    indirect=True,
)
@pytest.mark.parametrize("agent_biscuit", [ADDRESS_TWO], indirect=True)
def test_append_response_facts(agent_biscuit, request_facts):
    agent_kp = KeyPair()
    resp_facts = utils.new_response_facts(request_facts.req_id, b"hi", ADDRESS_ONE, 2)
    agent_biscuit = attenuate_for_response(agent_biscuit, resp_facts, agent_kp)

    assert agent_biscuit.block_count() == 2
