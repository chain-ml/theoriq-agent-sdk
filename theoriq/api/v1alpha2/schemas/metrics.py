from __future__ import annotations

from typing import Any, Dict, List, Sequence, Union

from theoriq.types import Metric


class MetricsRequestBody:
    def __init__(self, metrics: Union[List[Metric], Sequence[Metric], Metric]) -> None:
        self._metrics = [metrics] if isinstance(metrics, Metric) else metrics

    def to_dict(self) -> Dict[str, Any]:
        payload = {"metrics": [metric.to_dict() for metric in self._metrics]}
        return payload
