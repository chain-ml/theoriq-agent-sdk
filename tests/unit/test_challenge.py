import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from tests.unit.fixtures import *  # noqa: F403

from theoriq.agent import Agent, AgentDeploymentConfiguration


@pytest.fixture()
def challenge() -> bytes:
    """Generate a random challenge using the uuid package"""
    from uuid import uuid4

    return uuid4().bytes


def test_agent_challenge(
    agent_config: AgentDeploymentConfiguration, agent_public_key: Ed25519PublicKey, challenge: bytes
):
    agent = Agent(agent_config)
    signature = agent.sign_challenge(challenge)
    agent_public_key.verify(signature, challenge)
