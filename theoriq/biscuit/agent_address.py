"""Theoriq types"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from biscuit_auth import Authorizer, Biscuit, BiscuitBuilder, Check, Policy, PublicKey, Rule
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

    def new_authority_builder(self, expires_at: Optional[datetime] = None) -> BiscuitBuilder:
        """Creates a new authority block builder."""
        expires_at = expires_at or datetime.now(tz=timezone.utc) + timedelta(days=1)
        expiration_timestamp = int(expires_at.timestamp())
        return BiscuitBuilder(
            """
            theoriq:subject("agent", {agent_addr});
            theoriq:expires_at({expires_at});
            """,
            {"agent_addr": str(self.address), "expires_at": expiration_timestamp},
        )

    def default_authorizer(self) -> Authorizer:
        """
        Build an authorizer object for Biscuit authorization.
        :return: Authorizer object
        """
        authorizer = Authorizer()

        # Add subject address policy
        subject_addr_policy = Policy(
            """allow if theoriq:subject("agent", {agent_addr})""", {"agent_addr": self.address}
        )
        authorizer.add_policy(subject_addr_policy)

        # Add expiration check
        now = int(datetime.now(timezone.utc).timestamp())
        expiration_check = Check("check if theoriq:expires_at($time), $time > {now}", {"now": now})
        authorizer.add_check(expiration_check)

        return authorizer

    @classmethod
    def from_public_key(cls, key: PublicKey) -> AgentAddress:
        """
        Create an agent address from a public key
        :param key: public key
        :return: agent address
        """
        key_hash = keccak_256(bytes(key.to_bytes())).hexdigest()
        return cls(key_hash)

    @classmethod
    def from_biscuit(cls, biscuit: Biscuit) -> AgentAddress:
        """
        Create an agent address from a biscuit
        :param biscuit: biscuit
        :return: agent address
        """
        rule = Rule("""address($address) <- theoriq:subject("agent", $address)""")
        authorizer = Authorizer()
        authorizer.add_token(biscuit)
        facts = authorizer.query(rule)
        return cls(facts[0].terms[0])
