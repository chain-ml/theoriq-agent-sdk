from __future__ import annotations

from enum import Enum
from typing import Any


class Currency(Enum):
    USDC = "USDC"
    USDT = "USDT"

    @staticmethod
    def from_value(value: Any):
        try:
            if isinstance(value, str):
                if value.startswith("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"):
                    return Currency.USDC
                elif value.startswith("0xdAC17F958D2ee523a2206206994597C13D831ec7"):
                    return Currency.USDT
                return Currency(value)
            elif isinstance(value, Currency):
                return value
            else:
                raise ValueError(f"'{value}' is not a valid Currency")
        except ValueError as e:
            raise ValueError(f"'{value}' is not a valid Currency") from e
