from __future__ import annotations

from typing import Annotated, Optional

from pydantic import Field, field_validator, model_validator

from .block import BaseData, BlockBase


class CodeData(BaseData):
    code: str
    language: Optional[str] = None

    def to_str(self) -> str:
        if self.language:
            result = [f"```{self.language}", self.code, "```"]
        else:
            result = ["```", self.code, "```"]
        return "\n".join(result)

    def __str__(self) -> str:
        """
        Returns a string representation of the CodeItem instance.

        Returns:
            str: A string representing the CodeItem.
        """
        return f"CodeItem(code={self.code}, language={self.language})"


class CodeBlock(BlockBase[CodeData, Annotated[str, Field(pattern="code(:.*)?")]]):
    @field_validator("block_type")
    def validate_block_type(cls, v):
        if not v.startswith("code"):
            raise ValueError('CodeBlock block_type must start with "code"')
        return v

    @model_validator(mode="after")
    def set_language_from_block_type(self):
        if self.data and not self.data.language:
            language = self.sub_type(self.block_type)
            if language:
                self.data.language = language
        return self

    @classmethod
    def from_code(cls, code: str, language: Optional[str] = None) -> CodeBlock:
        block_type = f"code:{language}" if language else "code"
        return cls(block_type=block_type, data=CodeData(code=code, language=language))
