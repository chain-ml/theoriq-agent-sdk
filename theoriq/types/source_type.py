from __future__ import annotations

from enum import Enum
from typing import Any


class SourceType(Enum):
    User = "user"
    Agent = "agent"

    @staticmethod
    def from_value(value: Any):
        try:
            return SourceType(str(value))
        except ValueError as e:
            raise ValueError(f"'{value}' is not a valid SourceType") from e
