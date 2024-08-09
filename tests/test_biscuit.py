from datetime import datetime, timedelta, timezone
from typing import Final, Optional
from uuid import uuid4

import biscuit_auth
import pytest
from tests import utils
from theoriq.biscuit import AgentAddress, RequestFacts, ResponseFacts

ADDRESS_ONE: Final[AgentAddress] = AgentAddress.one()
ADDRESS_TWO: Final[AgentAddress] = AgentAddress.from_int(2)
ADDRESS_THREE: Final[AgentAddress] = AgentAddress.from_int(3)


@pytest.fixture
def agent_biscuit(request, biscuit_facts) -> biscuit_auth.Biscuit:
    def _biscuit_builder(subject_addr: AgentAddress, exp: Optional[datetime] = None) -> biscuit_auth.Biscuit:
        root_kp = biscuit_auth.KeyPair()
        expires_at = exp or datetime.now(tz=timezone.utc) + timedelta(hours=1)
        authority = subject_addr.new_authority_builder(expires_at=expires_at)
        authority.merge(biscuit_facts)
        return authority.build(root_kp.private_key)

    param = request.param
    return _biscuit_builder(**param) if isinstance(param, dict) else _biscuit_builder(param)


@pytest.fixture
def biscuit_facts(request_facts: RequestFacts, response_facts: ResponseFacts) -> biscuit_auth.BlockBuilder:
    return request_facts.to_block_builder() if response_facts is None else response_facts.to_block_builder()


@pytest.fixture
def request_facts(request) -> RequestFacts:
    if getattr(request, "param", None) is None:
        return utils.new_request_facts(b"Hello World", ADDRESS_ONE, ADDRESS_TWO, 10)
    else:
        (body, from_addr, to_addr, amount) = request.param
        return utils.new_request_facts(body, from_addr, to_addr, amount)


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
    authorizer = ADDRESS_TWO.default_authorizer()
    authorizer.add_token(agent_biscuit)
    authorizer.authorize()


@pytest.mark.parametrize("agent_biscuit", [ADDRESS_TWO], indirect=True)
def test_authorization_wrong_subject_address_raises_authorization_error(agent_biscuit):
    wrong_subject_address = AgentAddress.from_int(42)
    authorizer = wrong_subject_address.default_authorizer()
    authorizer.add_token(agent_biscuit)

    with pytest.raises(biscuit_auth.AuthorizationError):
        authorizer.authorize()


@pytest.mark.parametrize("agent_biscuit", [{"subject_addr": ADDRESS_TWO, "exp": one_hour_ago()}], indirect=True)
def test_authorization_expired_raises_authorization_error(agent_biscuit: biscuit_auth.Biscuit):
    authorizer = ADDRESS_TWO.default_authorizer()
    authorizer.add_token(agent_biscuit)

    with pytest.raises(biscuit_auth.AuthorizationError):
        authorizer.authorize()


@pytest.mark.parametrize(
    "request_facts",
    [
        (
            b"hello",
            str(ADDRESS_ONE),
            str(ADDRESS_TWO),
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
def test_append_request_facts(agent_biscuit: biscuit_auth.Biscuit):
    agent_kp = biscuit_auth.KeyPair()
    req_facts = utils.new_request_facts(b"help", ADDRESS_TWO, ADDRESS_THREE, 5)
    agent_biscuit = agent_biscuit.append_third_party_block(agent_kp, req_facts.to_block_builder())  # type: ignore

    assert agent_biscuit.block_count() == 2


@pytest.mark.parametrize(
    "request_facts",
    [
        (
            b"hello",
            str(ADDRESS_ONE),
            str(ADDRESS_TWO),
            10,
        )
    ],
    indirect=True,
)
@pytest.mark.parametrize("agent_biscuit", [ADDRESS_TWO], indirect=True)
def test_append_response_facts(agent_biscuit, request_facts):
    agent_kp = biscuit_auth.KeyPair()
    resp_facts = utils.new_response_facts(request_facts.req_id, b"hi", ADDRESS_ONE, 2)
    agent_biscuit = agent_biscuit.append_third_party_block(agent_kp, resp_facts.to_block_builder())  # type: ignore

    assert agent_biscuit.block_count() == 2
