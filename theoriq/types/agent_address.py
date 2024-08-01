"""Theoriq types"""

from __future__ import annotations

from biscuit_auth import PublicKey
from sha3 import keccak_256  # type: ignore
from theoriq.utils import verify_address


# TODO: Rename this class to AgentId
class AgentAddress:
    """
    Address of an agent registered on the `theoriq` protocol
    Agent's address must be a 32 bytes hex encoded string
    """

    def __init__(self, address: str) -> None:
        self.address = verify_address(address)

    def __str__(self) -> str:
        return self.address

    def __eq__(self, other: object) -> bool:
        if isinstance(other, AgentAddress):
            return self.address == other.address
        return False

    @classmethod
    def from_public_key(cls, key: PublicKey) -> AgentAddress:
        """
        Create an agent address from a public key
        :param key: public key
        :return: agent address
        """
        key_hash = keccak_256(bytes(key.to_bytes())).hexdigest()
        return cls(key_hash)
