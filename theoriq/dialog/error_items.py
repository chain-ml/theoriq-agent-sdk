from __future__ import annotations

from typing import Annotated, Literal, Optional

from .block import BaseData, BlockBase


class ErrorData(BaseData):
    err: str
    message: Optional[str]

    """
    A class representing an error item. Inherits from BaseData.
    """

    def to_str(self) -> str:
        result = [f"- Error: {self.err}"]
        if self.message is not None:
            result.append(f"- Message: {self.message}")
        return "\n".join(result)


class ErrorBlock(BlockBase[ErrorData, Annotated[str, Literal["error"]]]):

    @classmethod
    def from_error(cls, err: str, message: Optional[str] = None) -> ErrorBlock:
        return ErrorBlock(block_type="error", data=ErrorData(err=err, message=message))

    @classmethod
    def from_exception(cls, e: Exception) -> ErrorBlock:
        return ErrorBlock(block_type="error", data=ErrorData(err=str(e), message=None))
