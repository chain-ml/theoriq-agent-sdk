import json
import uuid

import flask
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
import pytest
from flask.testing import FlaskClient

import theoriq.flask_server
from biscuit_auth import KeyPair
from .utils import new_authority_block, new_req_facts

from theoriq.schemas import DialogItem, ChallengeResponseBody

from flask import Flask

from theoriq.agent import AgentConfig

from tests.fixtures import *  # noqa: F403


@pytest.fixture
def app(agent_config: AgentConfig) -> Flask:
    app = Flask(__name__)
    app.config["TESTING"] = True
    print("app", agent_config.agent_address)

    app.register_blueprint(theoriq.flask_server.theoriq_blueprint(agent_config, echo_last_prompt))

    return app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture
def runner(app: Flask):
    return app.test_cli_runner()


def test_sign_challenge(client: FlaskClient, agent_public_key: Ed25519PublicKey):
    nonce = uuid.uuid4().hex
    request_body = {"nonce": nonce}

    response = client.post("/theoriq/api/v1alpha1/system/challenge", json=request_body)

    assert response.status_code == 200

    challenge_response = ChallengeResponseBody.model_validate(response.json)
    signature = bytes.fromhex(challenge_response.signature)
    response_nonce = bytes.fromhex(challenge_response.nonce)
    agent_public_key.verify(signature, response_nonce)
    assert challenge_response.nonce == nonce


def test_execute_request(theoriq_kp, agent_kp, agent_config: AgentConfig, client: FlaskClient):
    # theoriq_kp = biscuit_auth.KeyPair()
    # agent_kp = biscuit_auth.KeyPair()

    # agent_config = AgentConfig(
    #     theoriq_kp.public_key,
    #     agent_kp.private_key,
    #     address=AgentAddress("0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")
    # )

    assert agent_config.theoriq_public_key.to_hex() == theoriq_kp.public_key.to_hex()
    assert KeyPair.from_private_key(agent_config.agent_private_key).public_key.to_hex() == agent_kp.public_key.to_hex()
    print("test", agent_config.agent_address)

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

    req_body_str = json.dumps(request_body)
    print(req_body_str)
    req_body_bytes = req_body_str.encode("utf-8")
    decoded_body = req_body_bytes.decode("utf-8")
    print(decoded_body)
    assert decoded_body == req_body_str
    # body_hash = hashlib.sha256(req_body_str.encode('utf-8')).hexdigest()

    # body = b"Hello World!"

    agent_address = agent_config.agent_address
    print(agent_address)
    authority = new_authority_block(agent_address)
    from_address = "012345689012345689012345689012345689"
    request_facts = new_req_facts(req_body_bytes, from_address, agent_address, 10)
    # request_facts = new_req_facts(body, from_address, agent_address, 10)
    authority.merge(request_facts.to_block())
    biscuit = authority.build(theoriq_kp.private_key)
    print("Sent", biscuit.to_base64())

    headers = {
        "Content-Type": "application/json",
        "Authorization": "bearer " + biscuit.to_base64(),
    }

    # TODO: Generate bearer token
    response = client.post("/theoriq/api/v1alpha1/execute", data=req_body_bytes, headers=headers)
    print(response.data)
    assert response.status_code == 200


def echo_last_prompt(items: list[DialogItem]) -> flask.Response:
    last_prompt = items[-1].items[0].data
    return flask.Response(last_prompt)
