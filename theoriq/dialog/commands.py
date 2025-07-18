from __future__ import annotations
from typing import Any, Generic, Literal, TypeVar, Union

from pydantic import BaseModel, field_validator

from theoriq.dialog.bloc import BlockBase

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
    command_name = command_data.get("name")
    if command_name == "search":
        return SearchCommandData(**command_data)
    return UnknownCommandData(name=command_name, arguments=command_data.get("arguments", {}))


T_CommandData = TypeVar("T_CommandData", bound=CommandData)


class CommandBlock(BlockBase[CommandData, Literal["command"]], Generic[T_Args, T_Name]):
    @classmethod
    def from_command(cls, command: UnknownCommandData) -> CommandBlock:
        return cls(block_type="command", data=command)

    @field_validator("data", mode="before")
    def parse_command_data(cls, v):
        if isinstance(v, dict):
            return parse_command_data(v)
        return v
