"""Common Fixtures used for testing"""

from typing import Optional

import pytest
from biscuit_auth import KeyPair
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from theoriq.agent import AgentConfig


@pytest.fixture(scope="function")
def theoriq_kp() -> KeyPair:
    """Generate a theoriq keypair"""
    return KeyPair()


@pytest.fixture
def agent_kp() -> KeyPair:
    """Generate an agent keypair"""
    return KeyPair()


@pytest.fixture
def agent_config(theoriq_kp: Optional[KeyPair], agent_kp: Optional[KeyPair]) -> AgentConfig:
    """
    Fixture creating an `AgentConfig` for testing purposes

    :param theoriq_kp: optional theoriq keypair, if not set a new one is generated
    :param agent_kp: optional agent keypair, if not set a new one is generated
    :return: new AgentConfig instance
    """

    theoriq_kp = KeyPair() if theoriq_kp is None else theoriq_kp
    agent_kp = KeyPair() if agent_kp is None else agent_kp

    return AgentConfig(theoriq_public_key=theoriq_kp.public_key, agent_kp=agent_kp)


@pytest.fixture
def agent_public_key(agent_config: AgentConfig) -> Ed25519PublicKey:
    agent_keypair = KeyPair.from_private_key(agent_config.agent_private_key)
    public_key_bytes = bytes(agent_keypair.public_key.to_bytes())
    return Ed25519PublicKey.from_public_bytes(public_key_bytes)


__all__ = ["theoriq_kp", "agent_kp", "agent_config", "agent_public_key"]
