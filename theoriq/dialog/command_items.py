from __future__ import annotations

from typing import Any, Generic, Literal, Type, TypeVar, Union, get_args, get_origin

from pydantic import BaseModel, field_validator

from .block import BaseData, BlockBase

T_Args = TypeVar("T_Args", bound=Union[BaseModel, dict[str, Any]])
T_Name = TypeVar("T_Name", bound=str)


class CommandData(BaseData, Generic[T_Args, T_Name]):
    name: T_Name
    arguments: T_Args

    def to_str(self) -> str:
        return f"- `{self.name}` command with arguments `{self.arguments}`"

    def __str__(self) -> str:
        return f"CommandItem(name={self.name}, arguments={self.arguments})"


UnknownCommandData = CommandData[dict[str, Any], str]


class SearchArgs(BaseModel):
    query: str

    def __str__(self) -> str:
        return self.model_dump_json()


class SearchCommandData(CommandData[SearchArgs, Literal["search"]]):
    pass


def parse_command_data(command_data: dict) -> CommandData:
    command_name = command_data.get("name", "unknown")
    if command_name == "search":
        return SearchCommandData(**command_data)
    return UnknownCommandData(name=command_name, arguments=command_data.get("arguments", {}))


_registry: dict[str, Type[CommandData]] = dict()

class CommandBlock(BlockBase[CommandData, Literal["command"]], Generic[T_Args, T_Name]):
    @classmethod
    def register(cls, command_data: Type[CommandData[T_Args, T_Name]]) -> None:
        values_ = get_args(command_data.model_fields["name"].annotation)
        for item in values_:
            _registry[item] = command_data

    @classmethod
    def from_command(cls, command: UnknownCommandData) -> CommandBlock:
        return cls(block_type="command", data=command)

    @field_validator("data", mode="before")
    def parse_command_data(cls, v):
        if isinstance(v, dict):
            command_name = v.get("name", "unknown")
            command_type = _registry.get(command_name, UnknownCommandData)
            return command_type(**v)
        return v
