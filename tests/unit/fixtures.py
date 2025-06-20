"""Common Fixtures used for testing"""

import os
from typing import Optional

import pytest
from biscuit_auth import KeyPair, PrivateKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from theoriq.api.v1alpha2.agent import AgentDeploymentConfiguration


@pytest.fixture(scope="function")
def theoriq_private_key() -> PrivateKey:
    """Generate a theoriq keypair"""
    kp = KeyPair()
    os.environ["THEORIQ_PUBLIC_KEY"] = kp.public_key.to_hex()
    os.environ["THEORIQ_URI"] = ""
    return kp.private_key


@pytest.fixture
def agent_kp() -> KeyPair:
    """Generate an agent keypair"""
    return KeyPair()


@pytest.fixture
def agent_config(agent_kp: Optional[KeyPair]) -> AgentDeploymentConfiguration:
    """
    Fixture creating an `AgentConfig` for testing purposes

    :param agent_kp: optional agent keypair, if not set a new one is generated
    :return: new AgentConfig instance
    """

    agent_kp = KeyPair() if agent_kp is None else agent_kp
    return AgentDeploymentConfiguration(private_key=agent_kp.private_key)


@pytest.fixture
def agent_public_key(agent_config: AgentDeploymentConfiguration) -> Ed25519PublicKey:
    agent_keypair = KeyPair.from_private_key(agent_config.private_key)
    public_key_bytes = bytes(agent_keypair.public_key.to_bytes())
    return Ed25519PublicKey.from_public_bytes(public_key_bytes)


__all__ = ["theoriq_private_key", "agent_kp", "agent_config", "agent_public_key"]
