from __future__ import annotations

from typing import Any, Generic, Literal, Sequence, Type, TypeVar, Union, get_args

from pydantic import BaseModel, field_validator

from .block import BaseData, BlockBase

T_Args = TypeVar("T_Args", bound=Union[BaseModel, dict[str, Any]])
T_Name = TypeVar("T_Name", bound=str)


class CommandData(BaseData, Generic[T_Args, T_Name]):
    name: T_Name
    arguments: T_Args

    @classmethod
    def get_names(cls: Type[CommandData[T_Args, T_Name]]) -> Sequence[str]:
        return get_args(cls.model_fields["name"].annotation)

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


_registry: dict[str, Type[CommandData]] = dict()


class CommandBlock(BlockBase[CommandData, Literal["command"]], Generic[T_Args, T_Name]):
    @staticmethod
    def register_command(command_data: Type[CommandData]) -> None:
        values_ = command_data.get_names()
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
