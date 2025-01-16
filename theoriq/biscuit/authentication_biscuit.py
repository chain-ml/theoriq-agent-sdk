from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from biscuit_auth import Biscuit

from theoriq import Agent
from theoriq.biscuit import AgentAddress


class AuthenticationFacts:
    """Required facts inside the Agent authentication biscuit"""

    def __init__(self, agent_address: AgentAddress):
        self.agent_address = agent_address

    @staticmethod
    def generate_new_biscuit(agent: Agent) -> AuthenticationBiscuit:
        agent_address = agent.config.address
        facts = AuthenticationFacts(agent_address)
        expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=5)
        builder = facts.agent_address.new_authority_builder(expires_at)
        private_key = agent.config.private_key
        biscuit = builder.build(private_key)
        return AuthenticationBiscuit(biscuit)

    def __str__(self):
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

    def __str__(self):
        return f"AuthenticationBiscuit(biscuit={self.biscuit})"
