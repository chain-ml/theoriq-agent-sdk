from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

from .item_block import BaseData, ItemBlock


class MetricItem(BaseData):
    """
    A class representing a single metric item. Inherits from BaseData.
    """

    def __init__(self, name: str, *, value: float, trend_percentage: float) -> None:
        """
        Initializes a MetricItem instance.

        Args:
            name (str): The name of the metric.
            value (float): The value of the metric.
            trend_percentage (float): The percentage change or trend for the metric.
        """
        self.name = name
        self.value = value
        self.trend_percentage = trend_percentage

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the MetricItem instance into a dictionary.

        Returns:
            Dict[str, Any]: A dictionary with the metric's name, value, and trend percentage.
        """
        return {"name": self.name, "value": self.value, "trendPercentage": self.trend_percentage}

    def to_str(self) -> str:
        result = [f"- Name: {self.name}", f"- Value: {self.value}", f"- TrendPercentage: {self.trend_percentage:.2f}%"]
        return "\n".join(result)

    @classmethod
    def from_dict(cls, values: Dict[str, Any]) -> MetricItem:
        """
        Creates an instance of MetricItem from a dictionary.

        Args:
            values (Dict[str, Any]): The dictionary containing the metric's name, value, and trend percentage.

        Returns:
            MetricItem: A new instance of MetricItem initialized with the provided values.
        """
        return cls(name=values["name"], value=values["value"], trend_percentage=values["trendPercentage"])

    def __str__(self):
        """
        Returns a string representation of the MetricItem instance.

        Returns:
            str: A string representing the MetricItem.
        """
        return f"MetricItem(name={self.name}, value={self.value}, trend_percentage={self.trend_percentage})"


class MetricsItemBlock(ItemBlock[Sequence[MetricItem]]):
    """
    A class representing a block of metric items. Inherits from ItemBlock with a sequence of MetricItem as the generic type.
    """

    def __init__(
        self, metrics: Sequence[MetricItem], key: Optional[str] = None, reference: Optional[str] = None
    ) -> None:
        """
        Initializes a MetricsItemBlock instance.

        Args:
            metrics (Sequence[MetricItem]): A sequence of MetricItem instances to be stored in the block.
        """
        super().__init__(block_type=MetricsItemBlock.block_type(), data=metrics, key=key, reference=reference)

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], block_type: str, block_key: Optional[str] = None, block_ref: Optional[str] = None
    ) -> MetricsItemBlock:
        """
        Creates an instance of MetricsItemBlock from a dictionary.

        Args:
            data (Dict[str, Any]): The dictionary containing the metrics.
            block_type (str): The type of the block.

        Returns:
            MetricsItemBlock: A new instance of MetricsItemBlock initialized with the provided data.
        """
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        items = data.get("items", [])
        return cls(metrics=[MetricItem.from_dict(metric) for metric in items], key=block_key, reference=block_ref)

    @staticmethod
    def block_type() -> str:
        """
        Returns the block type for MetricsItemBlock.

        Returns:
            str: The string 'metrics', representing the block type.
        """
        return "metrics"

    @staticmethod
    def is_valid(block_type: str) -> bool:
        """
        Checks if the provided block type is valid for a MetricsItemBlock.

        Args:
            block_type (str): The block type to validate.

        Returns:
            bool: True if the block type is valid, False otherwise.
        """
        return block_type == MetricsItemBlock.block_type()
