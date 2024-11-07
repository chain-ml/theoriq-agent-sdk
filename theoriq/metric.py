from typing import Any, Dict

from typing_extensions import Self


class Metric:
    def __init__(self, *, name: str, value: int) -> None:
        self.name = name
        self.value = value
        self._custom_labels: Dict[str, str] = {}

    def add_custom_label(self, name: str, value: str) -> Self:
        self._custom_labels[name] = value
        return self

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "name": self.name,
            "value": self.value,
        }
        if self._custom_labels:
            result["customLabels"] = self._custom_labels

        return result
