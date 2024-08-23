from __future__ import annotations

from typing import Any, Dict, Optional

from .schemas import BaseData, ItemBlock


class ErrorItem(BaseData):
    """ """

    def __init__(self, err: str, message: Optional[str]) -> None:
        self.err = err
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        result = {"error": self.err}
        if self.message:
            result["message"] = self.message
        return result

    @classmethod
    def from_dict(cls, values: Dict[str, Any]) -> ErrorItem:
        return cls(err=values["error"], message=values.get("message"))

    def __str__(self):
        return f"ErrorItem(err={self.err}, message={self.message})"


class ErrorItemBlock(ItemBlock[ErrorItem]):
    """ """

    def __init__(self, err: ErrorItem) -> None:
        super().__init__(bloc_type=ErrorItemBlock.block_type(), data=err)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], block_type: str) -> ErrorItemBlock:
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        values = data.get("error")
        if values is None:
            raise ValueError("Missing 'error' key")
        return cls(err=ErrorItem.from_dict(values))

    @classmethod
    def block_type(cls) -> str:
        return "error"

    @classmethod
    def is_valid(cls, block_type: str) -> bool:
        return block_type.startswith(ErrorItemBlock.block_type())

    @classmethod
    def new(cls, err: str, message: Optional[str]) -> ErrorItemBlock:
        return cls(err=ErrorItem(err=err, message=message))
