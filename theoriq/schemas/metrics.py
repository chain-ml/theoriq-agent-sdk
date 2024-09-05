from __future__ import annotations

from typing import Any, Dict, Sequence

from .schemas import BaseData, ItemBlock


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

    def __init__(self, metrics: Sequence[MetricItem], **kwargs) -> None:
        """
        Initializes a MetricsItemBlock instance.

        Args:
            metrics (Sequence[MetricItem]): A sequence of MetricItem instances to be stored in the block.
        """
        super().__init__(bloc_type=MetricsItemBlock.block_type(), data=metrics, **kwargs)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], block_type: str) -> MetricsItemBlock:
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
        # Converts each dictionary in 'items' into a MetricItem instance.
        return cls(metrics=[MetricItem.from_dict(metric) for metric in items])

    @classmethod
    def block_type(cls) -> str:
        """
        Returns the block type for MetricsItemBlock.

        Returns:
            str: The string 'metrics', representing the block type.
        """
        return "metrics"

    @classmethod
    def is_valid(cls, block_type: str) -> bool:
        """
        Checks if the provided block type is valid for a MetricsItemBlock.

        Args:
            block_type (str): The block type to validate.

        Returns:
            bool: True if the block type is valid, False otherwise.
        """
        return block_type == MetricsItemBlock.block_type()
