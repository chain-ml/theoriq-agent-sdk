from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

from theoriq.dialog import BaseData, ItemBlock


class CommandItem(BaseData):
    def __init__(self, name: str, arguments: Dict[str, Any]) -> None:
        self.name = name
        self.arguments = arguments

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CommandItem:
        return cls(name=data["name"], arguments=data.get("arguments", {}))

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "arguments": self.arguments}

    def to_str(self) -> str:
        return f"- `{self.name}` command with arguments `{self.arguments}`"

    def __str__(self) -> str:
        return f"CommandItem(name={self.name}, arguments={self.arguments})"


class CommandsItemBlock(ItemBlock[Sequence[CommandItem]]):
    def __init__(
        self, commands: Sequence[CommandItem], key: Optional[str] = None, reference: Optional[str] = None
    ) -> None:
        super().__init__(block_type=self.block_type(), data=commands, key=key, reference=reference)

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], block_type: str, block_key: Optional[str] = None, block_ref: Optional[str] = None
    ) -> CommandsItemBlock:
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        items = data.get("items", [])
        return cls(commands=[CommandItem.from_dict(item) for item in items], key=block_key, reference=block_ref)

    @staticmethod
    def block_type() -> str:
        return "command"

    @staticmethod
    def is_valid(block_type: str) -> bool:
        return block_type.startswith(CommandsItemBlock.block_type())
