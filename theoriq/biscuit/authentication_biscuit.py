from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from biscuit_auth import Biscuit, PrivateKey

from theoriq.biscuit import AgentAddress


class AuthenticationFacts:
    """Required facts inside the Agent authentication biscuit"""

    def __init__(self, address: AgentAddress, private_key: PrivateKey):
        self.agent_address = address
        self.private_key = private_key

    def to_authentication_biscuit(self) -> AuthenticationBiscuit:
        expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=5)
        builder = self.agent_address.new_authority_builder(expires_at)
        biscuit = builder.build(self.private_key)
        return AuthenticationBiscuit(biscuit)

    def __str__(self) -> str:
        return f"AuthenticationFacts(agent_address={self.agent_address})"


class AuthenticationBiscuit:
    """Agent authentication biscuit to be exchanged for an Agent biscuit"""

    def __init__(self, biscuit: Biscuit):
        self.biscuit: Biscuit = biscuit

    def to_base64(self) -> str:
        return self.biscuit.to_base64()

    def to_headers(self) -> Dict[str, Any]:
        return {
            "Content-Type": "application/json",
            "Authorization": "bearer " + self.biscuit.to_base64(),
        }

    def __str__(self) -> str:
        return f"AuthenticationBiscuit(biscuit={self.biscuit})"
