from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel

from .block import BaseData, BlockBase


class RouterItem(BaseModel):
    name: str
    score: float
    reason: Optional[str] = None


class RouterData(BaseData):
    items: List[RouterItem]


class RouterBlock(BlockBase[RouterData, Literal["router"]]):
    pass
