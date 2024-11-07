from typing import Any, Dict


class Metric:
    def __init__(self, *, name: str, value: int) -> None:
        self.name = name
        self.value = value
        self._custom_labels: Dict[str, int] = {}

    def add_custom_label(self, name: str, value: int) -> None:
        self._custom_labels[name] = value

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "name": self.name,
            "value": self.value,
        }
        if self._custom_labels:
            result["custom_labels"] = self._custom_labels

        return result
