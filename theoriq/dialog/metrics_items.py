from __future__ import annotations

from typing import Annotated, List, Literal

from pydantic import Field

from .block import BaseData, BlockBase


class MetricItem(BaseData):
    name: Annotated[str, Field(min_length=1, description="Metric name")]
    value: float
    trend_percentage: Annotated[float, Field(alias="trendPercentage")]

    class Config:
        populate_by_name = True


class MetricsData(BaseData):
    items: List[MetricItem]

    @classmethod
    def from_metric(cls, name: str, value: float, trend_percentage: float) -> MetricsData:
        return cls(items=[MetricItem(name=name, value=value, trend_percentage=trend_percentage)])


class MetricsBlock(BlockBase[MetricsData, Literal["metrics"]]):
    pass
