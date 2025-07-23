from __future__ import annotations

from typing import Annotated, List, Literal, Optional, TypeVar, Union

from pydantic import Field

from .block import BaseData, BlockBase
from .code_items import CodeBlock
from .command_items import CommandBlock
from .data_items import DataBlock
from .text_items import TextBlock

# Type alias for supported block types
SuggestionBlockTypes = Union[TextBlock, CodeBlock, CommandBlock, DataBlock]
T = TypeVar("T", bound=SuggestionBlockTypes)


class SuggestionItem(BaseData):
    agent_id: Optional[str] = None
    description: Annotated[str, Field(min_length=1, description="Block description")]
    block: SuggestionBlockTypes


class SuggestionsData(BaseData):
    items: List[SuggestionItem]

    @classmethod
    def from_suggestion(cls, description: str, block: T) -> SuggestionsData:
        return cls(items=[SuggestionItem(agent_id=None, description=description, block=block)])


class SuggestionsBlock(BlockBase[SuggestionsData, Literal["suggestions"]]):
    pass
