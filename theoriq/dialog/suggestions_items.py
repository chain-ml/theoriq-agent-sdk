from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, List, Literal, Optional, TypeVar, Union

from pydantic import Field

from .block import BaseData, BlockBase
from .code_items import CodeBlock
from .command_items import CommandBlock, UnknownCommandData
from .data_items import DataBlock
from .text_items import TextBlock

# Type alias for supported block types
SuggestionBlockTypes = Union[TextBlock, CodeBlock, CommandBlock, DataBlock]
T = TypeVar("T", bound=SuggestionBlockTypes)


class SuggestionItem(BaseData):
    agent_id: Optional[str] = None
    description: Annotated[str, Field(min_length=1, description="Block description")]
    block: SuggestionBlockTypes

    @classmethod
    def from_text(cls, agent_id: Optional[str] = None, *, description: str, text: str) -> SuggestionItem:
        return cls(agent_id=agent_id, description=description, block=TextBlock.from_text(text))

    @classmethod
    def from_command(
        cls, agent_id: Optional[str] = None, *, description: str, command: UnknownCommandData
    ) -> SuggestionItem:
        return cls(agent_id=agent_id, description=description, block=CommandBlock.from_command(command))


class SuggestionsData(BaseData):
    items: List[SuggestionItem]

    @classmethod
    def from_suggestion(cls, agent_id: Optional[str] = None, *, description: str, block: T) -> SuggestionsData:
        return cls(items=[SuggestionItem(agent_id=agent_id, description=description, block=block)])

    @classmethod
    def from_items(cls, items: Sequence[SuggestionItem]) -> SuggestionsData:
        return cls(items=list(items))


class SuggestionsBlock(BlockBase[SuggestionsData, Literal["suggestions"]]):

    @classmethod
    def from_suggestion(cls, agent_id: Optional[str] = None, *, description: str, block: T) -> SuggestionsBlock:
        return cls(
            block_type="suggestions",
            data=SuggestionsData.from_suggestion(agent_id=agent_id, description=description, block=block),
        )

    @classmethod
    def from_items(cls, items: Sequence[SuggestionItem]) -> SuggestionsBlock:
        return cls(block_type="suggestions", data=SuggestionsData.from_items(items=items))
