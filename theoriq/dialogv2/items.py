from __future__ import annotations
from typing import Optional, List, Literal, Any, TypeVar, Union, Generic, Annotated

from pydantic import BaseModel, Field, field_validator

from theoriq.dialog import CommandItemBlock


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

T_Args = TypeVar("T_Args", bound=Union[BaseModel, dict[str, Any]])
T_Name = TypeVar("T_Name", bound=str)

class CommandData(BaseModel, Generic[T_Args, T_Name]):
    name: T_Name
    arguments: T_Args

    def to_str(self) -> str:
        return f"- `{self.name}` command with arguments `{self.arguments}`"

    def __str__(self) -> str:
        return f"CommandItem(name={self.name}, arguments={self.arguments})"

UnknownCommandData = CommandData[dict[str, Any], str]

class SearchArgs(BaseModel):
    query: str

class SearchCommandData(CommandData[SearchArgs, Literal["search"]]):
    pass

def parse_command_data(command_data: dict) -> CommandData:
    command_name =  command_data.get("name")
    if command_name == "search":
        return SearchCommandData(**command_data)
    return UnknownCommandData(name = command_name, arguments = command_data.get("arguments", {}))

T_CommandData = TypeVar("T_CommandData", bound=CommandData)

class CommandBlock(BlockBase[CommandData[T_Args, T_Name], Literal["command"]], Generic[T_Args, T_Name]):
    @classmethod
    def from_command(cls, command: UnknownCommandData) -> CommandBlock:
        return cls(block_type="command", data=command)

    @field_validator("data", mode="before")
    def parse_command_data(cls, v):
        if isinstance(v, dict):
            return parse_command_data(v)
        return v

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

