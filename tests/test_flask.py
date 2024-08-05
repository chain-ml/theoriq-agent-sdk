import json
import uuid

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from flask import Flask
from flask.testing import FlaskClient
from tests.fixtures import *  # noqa: F403
from theoriq.agent import AgentConfig
from theoriq.biscuit import TheoriqCost
from theoriq.execute import ExecuteRequest, ExecuteResponse
from theoriq.extra.flask import theoriq_blueprint
from theoriq.schemas import ChallengeResponseBody, DialogItem
from theoriq.types.currency import Currency

from .utils import new_req_facts, new_request_biscuit


@pytest.fixture
def app(agent_config: AgentConfig) -> Flask:
    app = Flask(__name__)
    app.config["TESTING"] = True

    app.register_blueprint(theoriq_blueprint(agent_config, echo_last_prompt))
    return app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture
def runner(app: Flask):
    return app.test_cli_runner()


def test_send_sign_challenge(client: FlaskClient, agent_public_key: Ed25519PublicKey):
    nonce = uuid.uuid4().hex
    request_body = {"nonce": nonce}

    response = client.post("/theoriq/api/v1alpha1/system/challenge", json=request_body)

    assert response.status_code == 200

    challenge_response = ChallengeResponseBody.model_validate(response.json)
    signature = bytes.fromhex(challenge_response.signature)
    response_nonce = bytes.fromhex(challenge_response.nonce)
    agent_public_key.verify(signature, response_nonce)
    assert challenge_response.nonce == nonce


def test_send_execute_request(theoriq_kp, agent_kp, agent_config: AgentConfig, client: FlaskClient):
    request_body = {
        "items": [
            {
                "timestamp": "123",
                "sourceType": "user",
                "source": "0x012345689abcdef0123456789abcdef012345689abcdef0123456789abcdef01234567",
                "blocks": [{"data": {"text": "My name is John Doe"}, "type": "text"}],
            }
        ]
    }

    # Generate a request biscuit
    req_body_str = json.dumps(request_body)
    req_body_bytes = req_body_str.encode("utf-8")
    from_address = "012345689012345689012345689012345689"
    request_facts = new_req_facts(req_body_bytes, from_address, agent_config.agent_address, 10)
    req_biscuit = new_request_biscuit(request_facts, theoriq_kp)

    headers = {
        "Content-Type": "application/json",
        "Authorization": "bearer " + req_biscuit.to_base64(),
    }

    response = client.post("/theoriq/api/v1alpha1/execute", data=req_body_bytes, headers=headers)
    assert response.status_code == 200

    response_body = DialogItem.from_dict(response.json)
    assert response_body.blocks[0].data.text == "My name is John Doe"


def test_send_execute_request_without_biscuit_returns_401(
    theoriq_kp, agent_kp, agent_config: AgentConfig, client: FlaskClient
):
    request_body = {
        "items": [
            {
                "timestamp": "123",
                "sourceType": "user",
                "source": "0x012345689abcdef0123456789abcdef012345689abcdef0123456789abcdef01234567",
                "blocks": [{"data": {"text": "My name is John Doe"}, "type": "text"}],
            }
        ]
    }

    response = client.post("/theoriq/api/v1alpha1/execute", json=request_body)
    assert response.status_code == 401


def test_send_execute_request_with_ill_formatted_body_returns_400(
    theoriq_kp, agent_kp, agent_config: AgentConfig, client: FlaskClient
):
    request_body = {
        "items": [
            {
                "source": "0x012345689abcdef0123456789abcdef012345689abcdef0123456789abcdef01234567",
                "items": [{"data": "My name is John Doe", "type": "text"}],
            }
        ]
    }

    # Generate a request biscuit
    req_body_str = json.dumps(request_body)
    req_body_bytes = req_body_str.encode("utf-8")
    from_address = "012345689012345689012345689012345689"
    request_facts = new_req_facts(req_body_bytes, from_address, agent_config.agent_address, 10)
    req_biscuit = new_request_biscuit(request_facts, theoriq_kp)

    headers = {
        "Content-Type": "application/json",
        "Authorization": "bearer " + req_biscuit.to_base64(),
    }

    response = client.post("/theoriq/api/v1alpha1/execute", data=req_body_bytes, headers=headers)
    assert response.status_code == 400


def test_send_execute_request_when_execute_fn_fails_returns_500(
    theoriq_kp, agent_kp, agent_config: AgentConfig, client: FlaskClient
):
    request_body = {
        "items": [
            {
                "timestamp": "123",
                "sourceType": "user",
                "source": "0x012345689abcdef0123456789abcdef012345689abcdef0123456789abcdef01234567",
                "blocks": [{"data": {"text": "My name is John Doe should fail"}, "type": "text"}],
            }
        ]
    }

    # Generate a request biscuit
    req_body_str = json.dumps(request_body)
    req_body_bytes = req_body_str.encode("utf-8")
    from_address = "012345689012345689012345689012345689"
    request_facts = new_req_facts(req_body_bytes, from_address, agent_config.agent_address, 10)
    req_biscuit = new_request_biscuit(request_facts, theoriq_kp)

    headers = {
        "Content-Type": "application/json",
        "Authorization": "bearer " + req_biscuit.to_base64(),
    }

    response = client.post("/theoriq/api/v1alpha1/execute", data=req_body_bytes, headers=headers)
    print(response.headers)
    assert response.status_code == 500


def test_send_chat_completion_request(theoriq_kp, agent_kp, agent_config: AgentConfig, client: FlaskClient):
    request_body = {
        "items": [
            {
                "timestamp": "123",
                "sourceType": "user",
                "source": "0x012345689abcdef0123456789abcdef012345689abcdef0123456789abcdef01234567",
                "blocks": [{"data": {"text": "My name is John Doe"}, "type": "text"}],
            }
        ]
    }

    # Generate a request biscuit
    req_body_str = json.dumps(request_body)
    req_body_bytes = req_body_str.encode("utf-8")
    from_address = "012345689012345689012345689012345689"
    request_facts = new_req_facts(req_body_bytes, from_address, agent_config.agent_address, 10)
    req_biscuit = new_request_biscuit(request_facts, theoriq_kp)

    headers = {
        "Content-Type": "application/json",
        "Authorization": "bearer " + req_biscuit.to_base64(),
    }

    response = client.post("/api/v1alpha1/behaviors/chat-completion", data=req_body_bytes, headers=headers)
    assert response.status_code == 200

    response_body = DialogItem.from_dict(response.json)
    assert response_body.blocks[0].data.text == "My name is John Doe"


def echo_last_prompt(request: ExecuteRequest) -> ExecuteResponse:
    assert request.biscuit.request_facts.budget.amount == "10"
    last_prompt = request.body.items[-1].blocks[0].data.text

    if "should fail" in last_prompt:
        raise Exception("Execute function fails")

    response_body = DialogItem.new_text(source="My Test Agent", text=last_prompt)
    return ExecuteResponse(response_body, TheoriqCost(amount="5", currency=Currency.USDC))
