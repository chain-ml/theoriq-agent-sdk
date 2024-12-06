import json
import uuid

import pytest
from biscuit_auth import PrivateKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from flask import Flask
from flask.testing import FlaskClient
from tests.unit.fixtures import *  # noqa: F403

from theoriq.agent import AgentDeploymentConfiguration
from theoriq.api.common import ExecuteResponse
from theoriq.api.v1alpha1.execute import ExecuteContext
from theoriq.api.v1alpha1.schemas import ChallengeResponseBody, ExecuteRequestBody
from theoriq.biscuit import AgentAddress, TheoriqCost
from theoriq.dialog import DialogItem
from theoriq.extra.flask.v1alpha1.flask import theoriq_blueprint
from theoriq.types import Currency, SourceType

from .. import OsEnviron
from .utils import new_biscuit_for_request, new_request_facts


@pytest.fixture
def app(agent_config: AgentDeploymentConfiguration) -> Flask:
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

    response = client.post("/api/v1alpha1/system/challenge", json=request_body)
    assert response.status_code == 200

    challenge_response = ChallengeResponseBody.model_validate(response.json)
    signature = bytes.fromhex(challenge_response.signature.removeprefix("0x"))
    response_nonce = bytes.fromhex(challenge_response.nonce)
    agent_public_key.verify(signature, response_nonce)
    assert challenge_response.nonce == nonce


def test_send_execute_request(
    theoriq_private_key: PrivateKey, agent_kp, agent_config: AgentDeploymentConfiguration, client: FlaskClient
):

    with OsEnviron("THEORIQ_URI", "http://mock_flask_test"):
        from_address = AgentAddress.random()
        req_body_bytes = _build_request_body_bytes("My name is John Doe", from_address)
        request_facts = new_request_facts(req_body_bytes, from_address, agent_config.address, 10)
        req_biscuit = new_biscuit_for_request(request_facts, theoriq_private_key)
        response = client.post("/api/v1alpha1/execute", data=req_body_bytes, headers=req_biscuit.to_headers())
        assert response.status_code == 200

        response_body = DialogItem.from_dict(response.json)
        assert response_body.blocks[0].data.text == "My name is John Doe"


def test_send_execute_request_without_biscuit_returns_401(
    agent_kp, agent_config: AgentDeploymentConfiguration, client: FlaskClient
):
    with OsEnviron("THEORIQ_URI", "http://mock_flask_test"):
        request_body_bytes = _build_request_body_bytes("My name is John Doe", AgentAddress.one())
        response = client.post("/api/v1alpha1/execute", data=request_body_bytes)
        assert response.status_code == 401


def test_send_execute_request_with_ill_formatted_body_returns_400(
    theoriq_private_key: PrivateKey, agent_config: AgentDeploymentConfiguration, client: FlaskClient
):
    with OsEnviron("THEORIQ_URI", "http://mock_flask_test"):
        from_address = AgentAddress("012345689abcdef0123456789abcdef012345689abcdef0123456789abcdef01")
        request_body = {
            "items": [
                {
                    "source": str(from_address),
                    "items": [{"data": "My name is John Doe", "type": "text"}],
                }
            ]
        }

        # Generate a request biscuit
        req_body_bytes = json.dumps(request_body).encode("utf-8")
        request_facts = new_request_facts(req_body_bytes, from_address, agent_config.address, 10)
        req_biscuit = new_biscuit_for_request(request_facts, theoriq_private_key)
        response = client.post("/api/v1alpha1/execute", data=req_body_bytes, headers=req_biscuit.to_headers())
        assert response.status_code == 400


def test_send_execute_request_when_execute_fn_fails_returns_500(
    theoriq_private_key, agent_config: AgentDeploymentConfiguration, client: FlaskClient
):
    with OsEnviron("THEORIQ_URI", "http://mock_flask_test"):
        from_address = AgentAddress("012345689abcdef0123456789abcdef012345689abcdef0123456789abcdef01")
        req_body_bytes = _build_request_body_bytes("My name is John Doe should fail", from_address)

        # Generate a request biscuit
        request_facts = new_request_facts(req_body_bytes, from_address, agent_config.address, 10)
        req_biscuit = new_biscuit_for_request(request_facts, theoriq_private_key)
        response = client.post("/api/v1alpha1/execute", data=req_body_bytes, headers=req_biscuit.to_headers())
        print(response.headers)
        assert response.status_code == 500


def test_send_chat_completion_request(
    theoriq_private_key: PrivateKey, agent_config: AgentDeploymentConfiguration, client: FlaskClient
):
    with OsEnviron("THEORIQ_URI", "http://mock_flask_test"):
        from_address = AgentAddress("012345689abcdef0123456789abcdef012345689abcdef0123456789abcdef01")
        req_body_bytes = _build_request_body_bytes("My name is John Doe", from_address)
        request_facts = new_request_facts(req_body_bytes, from_address, agent_config.address, 10)
        req_biscuit = new_biscuit_for_request(request_facts, theoriq_private_key)

        response = client.post("/api/v1alpha1/execute", data=req_body_bytes, headers=req_biscuit.to_headers())
        assert response.status_code == 200

        response_body = DialogItem.from_dict(response.json)
        assert response_body.blocks[0].data.text == "My name is John Doe"


def echo_last_prompt(context: ExecuteContext, request: ExecuteRequestBody) -> ExecuteResponse:
    assert context.budget.amount == "10"
    last_prompt = request.last_item.blocks[0].data.text if request.last_item else "should fail"

    if "should fail" in last_prompt:
        raise RuntimeError("Execute function fails")

    response_body = DialogItem.new_text(source="My Test Agent", text=last_prompt)
    return ExecuteResponse(response_body, TheoriqCost(amount="5", currency=Currency.USDC))


def _build_request_body_bytes(text: str, source: AgentAddress) -> bytes:
    body = {
        "dialog": {
            "items": [
                {
                    "timestamp": "2024-08-07T00:00:00.000000+00:00",
                    "sourceType": SourceType.User.value,
                    "source": str(source),
                    "blocks": [{"data": {"text": text}, "type": "text:markdown"}],
                }
            ]
        }
    }
    return json.dumps(body).encode("utf-8")
