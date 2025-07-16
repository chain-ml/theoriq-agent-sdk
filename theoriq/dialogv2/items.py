from __future__ import annotations
from typing import Optional, List, Literal, Any, TypeVar, Union, Generic, Annotated

from pydantic import BaseModel, Field


class RouterItem(BaseModel):
    name: str
    score: float
    reason: Optional[str] = None


class RouterData(BaseModel):
    items: List[RouterItem]


class TextData(BaseModel):
    text: str


class CodeData(BaseModel):
    code: str


class CommandData(BaseModel):
    name: str
    arguments: dict[str, Any]

    def to_str(self) -> str:
        return f"- `{self.name}` command with arguments `{self.arguments}`"

    def __str__(self) -> str:
        return f"CommandItem(name={self.name}, arguments={self.arguments})"


T_Data = TypeVar("T_Data", bound=Union[BaseModel, dict[str, Any]])
T_Type = TypeVar("T_Type", bound=str)


class BlockBase(BaseModel, Generic[T_Data, T_Type]):
    ref: Annotated[Optional[str], Field(default=None)] = None
    key: Annotated[Optional[str], Field(default=None)] = None
    block_type: Annotated[T_Type, Field(alias="type")]
    data: T_Data

    class Config:
        populate_by_name = True

    def model_dump_json(self, **kwargs):
        """Override to ensure proper JSON serialization"""
        # Set default serialization options
        kwargs.setdefault("by_alias", True)
        kwargs.setdefault("exclude_none", True)
        kwargs.setdefault("exclude_defaults", True)
        kwargs.setdefault("exclude_unset", True)
        return super().model_dump_json(**kwargs)


class CommandBlock(BlockBase[CommandData, Literal["command"]]):
    @classmethod
    def from_command(cls, command: CommandData) -> CommandBlock:
        return cls(block_type="command", data=command)


class MetricItem(BaseModel):
    name: str
    value: float
    trendPercentage: float


class MetricsData(BaseModel):
    items: List[MetricItem]


class RouterBlock(BlockBase[RouterData, Literal["router"]]):
    pass


class TextBlock(BlockBase[TextData, Literal["text", "text:markdown"]]):

    @classmethod
    def from_text(cls, text: str, block_type: Literal["text"] = "text") -> TextBlock:
        return TextBlock(block_type=block_type, data=TextData(text=text))


class CodeBlock(BlockBase[CodeData, Literal["code"]]):
    pass


class MetricsBlock(BlockBase[MetricsData, Literal["metrics"]]):
    pass

