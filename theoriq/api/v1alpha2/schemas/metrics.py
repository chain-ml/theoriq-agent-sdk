from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from theoriq.types import Metric


class MetricsRequestBody:
    def __init__(self, metrics: Union[List[Metric], Metric]) -> None:
        self._metrics = metrics if isinstance(metrics, List) else [metrics]

    def to_dict(self) -> Dict[str, Any]:
        payload = {"metrics": [metric.to_dict() for metric in self._metrics]}
        return payload


class MetricResponse:
    def __init__(self, timestamp: datetime, name: str, value: int, custom_labels: Optional[Dict[str, str]]) -> None:
        self.timestamp = timestamp
        self.name = name
        self.value = value
        self.custom_labels = custom_labels if custom_labels is not None else {}

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> MetricResponse:
        return MetricResponse(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            name=data["name"],
            value=data["value"],
            custom_labels=data.get("customLabels"),
        )

    def to_metric(self) -> Metric:
        return Metric(name=self.name, value=self.value, custom_labels=self.custom_labels)

    def __str__(self) -> str:
        return f"MetricResponse(name={self.name}, value={self.value}, timestamp={self.timestamp})"
