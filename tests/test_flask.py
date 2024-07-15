import uuid

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
import pytest
from flask.testing import FlaskClient

import theoriq.flask_server
import biscuit_auth
from theoriq.types import AgentAddress

from flask import Flask

from theoriq.agent import AgentConfig

from .utils import agent_config, agent_public_key


@pytest.fixture
def app(agent_config: AgentConfig) -> Flask:
    app = Flask(__name__)
    app.config["TESTING"] = True

    app.register_blueprint(theoriq.flask_server.theoriq_blueprint(agent_config))

    yield app


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

    response_body = response.json
    signature = bytes.fromhex(response_body["signature"])
    response_nonce = bytes.fromhex(response_body["nonce"])
    agent_public_key.verify(signature, response_nonce)
    assert response_body["nonce"] == nonce
