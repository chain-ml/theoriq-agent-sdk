from __future__ import annotations

from enum import Enum
from typing import Any


class Currency(Enum):
    USDC = "USDC"
    USDT = "USDT"

    @staticmethod
    def from_value(value: Any):
        try:
            return Currency(str(value))
        except ValueError as e:
            raise ValueError(f"'{value}' is not a valid Currency") from e
