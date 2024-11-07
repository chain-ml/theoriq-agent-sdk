from typing import Any, Dict, Optional
from typing_extensions import Self


class Metric:
    """
    A class representing a metric with a name, value, and optional custom labels.

    Attributes:
        name (str): The name of the metric.
        value (int): The integer value of the metric.
        _custom_labels (Dict[str, str]): A dictionary for storing custom labels as key-value pairs.

    Methods:
        add_custom_label(name: str, value: str) -> Self:
            Adds a custom label to the metric and returns the instance for chaining.

        to_dict() -> Dict[str, Any]:
            Converts the Metric instance into a dictionary format, including custom labels if they exist.
    """

    def __init__(self, *, name: str, value: int, custom_labels: Optional[Dict[str, str]] = None) -> None:
        """
        Initializes a Metric instance with a specified name and value.

        Args:
            name (str): The name of the metric.
            value (int): The value associated with the metric.
        """
        self.name = name
        self.value = value
        self._custom_labels: Dict[str, str] = custom_labels if custom_labels is not None else {}

    def add_custom_label(self, name: str, value: str) -> Self:
        """
        Adds a custom label to the metric.

        Args:
            name (str): The name of the custom label.
            value (str): The value of the custom label.

        Returns:
            Self: The instance of Metric to allow for method chaining.
        """
        self._custom_labels[name] = value
        return self

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the Metric instance to a dictionary, including custom labels if they are present.

        Returns:
            Dict[str, Any]: A dictionary representation of the metric, including custom labels if available.
        """
        result: Dict[str, Any] = {
            "name": self.name,
            "value": self.value,
        }
        if self._custom_labels:
            result["customLabels"] = self._custom_labels

        return result
