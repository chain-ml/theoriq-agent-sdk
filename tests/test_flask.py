import json
import uuid

import flask
from biscuit_auth.biscuit_auth import Biscuit, KeyPair
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
import pytest
from flask.testing import FlaskClient

import theoriq_extra.flask

from theoriq.facts import TheoriqCost, ResponseFacts
from theoriq.types import ResponseBiscuit
from .utils import new_req_facts, new_req_biscuit

from theoriq.schemas import ChallengeResponseBody

from flask import Flask

from theoriq.agent import AgentConfig

from tests.fixtures import *  # noqa: F403


@pytest.fixture
def app(agent_config: AgentConfig) -> Flask:
    app = Flask(__name__)
    app.config["TESTING"] = True

    app.register_blueprint(theoriq_extra.flask.theoriq_blueprint(agent_config, echo_last_prompt))

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
                "items": [{"data": "My name is John Doe", "type": "text"}],
            }
        ]
    }

    # Generate a request biscuit
    req_body_str = json.dumps(request_body)
    req_body_bytes = req_body_str.encode("utf-8")
    from_address = "012345689012345689012345689012345689"
    request_facts = new_req_facts(req_body_bytes, from_address, agent_config.agent_address, 10)
    req_biscuit = new_req_biscuit(request_facts, theoriq_kp)

    headers = {
        "Content-Type": "application/json",
        "Authorization": "bearer " + req_biscuit.to_base64(),
    }

    response = client.post("/theoriq/api/v1alpha1/execute", data=req_body_bytes, headers=headers)
    assert response.status_code == 200
    assert response.json == "My name is John Doe"


def echo_last_prompt() -> flask.Response:
    execute_request = theoriq_extra.flask.execute_request_var.get()
    assert execute_request.biscuit.req_facts.budget.amount == "10"
    last_prompt = execute_request.body.items[-1].items[0].data
    theoriq_extra.flask.execute_response_cost_var.set(TheoriqCost(amount="5", currency="BTC"))
    return flask.jsonify(last_prompt)
