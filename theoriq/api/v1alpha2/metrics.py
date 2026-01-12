from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Sequence

from theoriq.api.v1alpha2 import ProtocolClient
from theoriq.api.v1alpha2.protocol.biscuit_provider import BiscuitProvider, BiscuitProviderFactory
from theoriq.types import Metric


class AgentMetricsPublisher:
    """Manages publishing agent metrics."""

    def __init__(self, biscuit_provider: BiscuitProvider, client: Optional[ProtocolClient] = None) -> None:
        self._client = client or ProtocolClient.from_env()
        self._biscuit_provider = biscuit_provider

    def publish(self, metrics: Sequence[Metric]) -> None:
        biscuit = self._biscuit_provider.get_biscuit()
        self._client.post_agent_metrics(biscuit, self._biscuit_provider.address, metrics=list(metrics))

    @classmethod
    def from_env(cls, env_prefix: str = "") -> AgentMetricsPublisher:
        return AgentMetricsPublisher(biscuit_provider=BiscuitProviderFactory.from_env(env_prefix=env_prefix))


class AgentMetricsReader:
    """Manages reading agent metrics."""

    def __init__(self, client: Optional[ProtocolClient] = None) -> None:
        self._client = client or ProtocolClient.from_env()

    def query(
        self,
        *,
        agent_id: str,
        name: str,
        submitted_after: Optional[datetime] = None,
        submitted_before: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Metric]:
        return self._client.get_agent_metrics(
            agent_id=agent_id,
            name=name,
            submitted_after=submitted_after,
            submitted_before=submitted_before,
            limit=limit,
        )
