from __future__ import annotations

from typing import Optional, Sequence

from theoriq.api.v1alpha2 import ProtocolClient
from theoriq.api.v1alpha2.protocol.biscuit_provider import BiscuitProvider, BiscuitProviderFactory
from theoriq.types import Metric


class AgentMetricsReporter:
    """Manages publishing agent metrics."""

    def __init__(self, biscuit_provider: BiscuitProvider, client: Optional[ProtocolClient] = None) -> None:
        self._client = client or ProtocolClient.from_env()
        self._biscuit_provider = biscuit_provider

    def post_metrics(self, metrics: Sequence[Metric]) -> None:
        biscuit = self._biscuit_provider.get_biscuit()
        self._client.post_agent_metrics(biscuit, self._biscuit_provider.address, metrics=list(metrics))

    def post_metric(self, metric: Metric) -> None:
        self.post_metrics([metric])

    @classmethod
    def from_env(cls, env_prefix: str = "") -> AgentMetricsReporter:
        return AgentMetricsReporter(biscuit_provider=BiscuitProviderFactory.from_env(env_prefix=env_prefix))
