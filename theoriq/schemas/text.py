from __future__ import annotations

from typing import Any, Dict, Optional

from .schemas import BaseData, ItemBlock


class TextItem(BaseData):
    """ """

    def __init__(self, text: str) -> None:
        self.text = text

    def to_dict(self) -> Dict[str, Any]:
        return {"text": self.text}


class TextItemBlock(ItemBlock[TextItem]):
    """ """

    def __init__(self, text: str, sub_type: Optional[str] = None) -> None:
        sub_type = f":{sub_type}" if sub_type is not None else ""
        super().__init__(bloc_type=f"{TextItemBlock.block_type()}{sub_type}", data=TextItem(text=text))

    @classmethod
    def from_dict(cls, data: Dict[str, Any], block_type: str) -> TextItemBlock:
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        return cls(text=data["text"], sub_type=cls.sub_type(block_type))

    @classmethod
    def block_type(cls) -> str:
        return "text"

    @classmethod
    def is_valid(cls, block_type: str) -> bool:
        return block_type.startswith(TextItemBlock.block_type())
