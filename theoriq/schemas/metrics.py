from __future__ import annotations

from typing import Any, Dict, Sequence

from .schemas import BaseData, ItemBlock


class MetricItem(BaseData):
    """ """

    def __init__(self, name: str, *, value: float, trend_percentage: float) -> None:
        self.name = name
        self.value = value
        self.trend_percentage = trend_percentage

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "value": self.value, "trendPercentage": self.trend_percentage}

    @classmethod
    def from_dict(cls, values: Dict[str, Any]) -> MetricItem:
        return cls(name=values["name"], value=values["value"], trend_percentage=values["trendPercentage"])

    def __str__(self):
        return f"MetricItem(name={self.name}, value={self.value}, trend_percentage={self.trend_percentage})"


class MetricsItemBlock(ItemBlock[Sequence[MetricItem]]):
    """ """

    def __init__(self, metrics: Sequence[MetricItem]) -> None:
        super().__init__(bloc_type=MetricsItemBlock.block_type(), data=metrics)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], block_type: str) -> MetricsItemBlock:
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        items = data.get("items", [])
        return cls(metrics=[MetricItem.from_dict(metric) for metric in items])

    @staticmethod
    def block_type() -> str:
        return "metrics"

    @classmethod
    def is_valid(cls, block_type: str) -> bool:
        return block_type == MetricsItemBlock.block_type()
