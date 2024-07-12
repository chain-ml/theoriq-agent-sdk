import pytest
import biscuit_auth

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from theoriq.agent import Agent, AgentConfig, AgentAddress


@pytest.fixture
def mock_agent_config() -> AgentConfig:
    theoriq_public_key = biscuit_auth.KeyPair()
    agent_keypair = biscuit_auth.KeyPair()

    return AgentConfig(
        theoriq_public_key=theoriq_public_key.public_key,
        private_key=agent_keypair.private_key,
        address=AgentAddress("0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"),
    )


@pytest.fixture()
def agent_public_key(mock_agent_config: AgentConfig) -> Ed25519PublicKey:
    agent_keypair = biscuit_auth.KeyPair.from_private_key(mock_agent_config.agent_private_key)
    public_key_bytes = bytes(agent_keypair.public_key.to_bytes())
    return Ed25519PublicKey.from_public_bytes(public_key_bytes)


@pytest.fixture()
def challenge() -> bytes:
    """Generate a random challenge using the uuid package"""
    from uuid import uuid4

    return uuid4().bytes


def test_agent_challenge(mock_agent_config: AgentConfig, agent_public_key: Ed25519PublicKey, challenge: bytes):
    agent = Agent(mock_agent_config)
    signature = agent.sign_challenge(challenge)
    agent_public_key.verify(signature, challenge)
