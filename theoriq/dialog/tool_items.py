from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from .block import BaseData, BlockBase


class ToolCallData(BaseData):
    name: Annotated[str, Field(..., description="Name of the tool to call")]
    arguments: Annotated[str, Field(..., description="JSON string of arguments to pass to the tool")]
    id: Annotated[str, Field(..., description="ID of the tool call")]


class ToolCallBlock(BlockBase[ToolCallData, Literal["internal:tool_call"]]):
    @classmethod
    def from_data(cls, *, name: str, arguments: str, id: str) -> ToolCallBlock:
        return ToolCallBlock(block_type="internal:tool_call", data=ToolCallData(name=name, arguments=arguments, id=id))


class ToolCallResultData(BaseData):
    content: Annotated[str, Field(..., description="Content of the tool call result")]
    id: Annotated[str, Field(..., description="ID of the tool call")]


class ToolCallResultBlock(BlockBase[ToolCallResultData, Literal["internal:tool_call_result"]]):
    @classmethod
    def from_data(cls, *, content: str, id: str) -> ToolCallResultBlock:
        return ToolCallResultBlock(
            block_type="internal:tool_call_result", data=ToolCallResultData(content=content, id=id)
        )
