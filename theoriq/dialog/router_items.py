from __future__ import annotations

from typing import Annotated, List, Literal, Optional

from pydantic import Field

from .block import BaseData, BlockBase


class RouterItem(BaseData):
    name: Annotated[str, Field(min_length=1, description="Name of the route")]
    score: Annotated[float, Field(default=0.0, ge=0.0, le=1.0, description="Score between 0 and 1")]
    reason: Optional[str] = None


class RouterData(BaseData):
    items: List[RouterItem]


class RouterBlock(BlockBase[RouterData, Literal["router"]]):
    pass
