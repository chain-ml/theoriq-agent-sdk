from __future__ import annotations

from enum import Enum
from typing import Any, Optional


class Currency(Enum):
    USDC = "USDC"
    USDT = "USDT"

    @classmethod
    def _missing_(cls, value: Any) -> Optional[Currency]:
        if isinstance(value, str):
            if value.startswith("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"):
                return Currency.USDC
            elif value.startswith("0xdAC17F958D2ee523a2206206994597C13D831ec7"):
                return Currency.USDT

            return cls.__members__.get(value.upper(), None)
        return None
