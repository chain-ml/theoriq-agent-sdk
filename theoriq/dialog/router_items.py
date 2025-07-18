from __future__ import annotations

from typing import List, Literal, Optional

from .block import BaseData, BlockBase


class RouterItem(BaseData):
    name: str
    score: float
    reason: Optional[str] = None


class RouterData(BaseData):
    items: List[RouterItem]


class RouterBlock(BlockBase[RouterData, Literal["router"]]):
    pass
