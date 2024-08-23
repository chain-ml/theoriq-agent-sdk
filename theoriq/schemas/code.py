from __future__ import annotations

from typing import Any, Dict, Optional

from .schemas import BaseData, ItemBlock


class CodeItem(BaseData):
    """ """

    def __init__(self, code: str) -> None:
        self.code = code

    def to_dict(self) -> Dict[str, Any]:
        return {"code": self.code}


class CodeItemBlock(ItemBlock[CodeItem]):
    """ """

    def __init__(self, *, code: str, language: Optional[str] = None) -> None:
        sub_type = f":{language}" if language is not None else ""
        super().__init__(bloc_type=f"{CodeItemBlock.block_type()}{sub_type}", data=CodeItem(code=code))

    @classmethod
    def from_dict(cls, data: Any, block_type: str) -> CodeItemBlock:
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        return cls(code=data["code"], language=cls.sub_type(block_type))

    @classmethod
    def block_type(cls) -> str:
        return "code"

    @staticmethod
    def is_valid(block_type: str) -> bool:
        return block_type.startswith(CodeItemBlock.block_type())
