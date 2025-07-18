from __future__ import annotations

from typing import Annotated, Optional

from pydantic import Field, field_validator, model_validator

from .block import BaseData, BlockBase


class TextData(BaseData):
    text: str
    type: Optional[str] = None

    def to_str(self) -> str:
        if self.type is None:
            return self.text
        result = [f"```{self.type}", self.text, "```"]
        return "\n".join(result)

    def __str__(self) -> str:
        """
        Returns a string representation of the TextItem instance.

        Returns:
            str: A string representing the TextItem.
        """
        return f"TextItem(text={self.text}, type={self.type})"


class TextBlock(BlockBase[TextData, Annotated[str, Field(pattern="text(:.*)?")]]):
    @field_validator("block_type")
    def validate_block_type(cls, v):
        if not v.startswith("text"):
            raise ValueError('TextBlock block_type must start with "text"')
        return v

    @model_validator(mode="after")
    def set_text_type_from_block_type(self):
        if self.data and not self.data.type:
            text_type = self.sub_type(self.block_type)
            if text_type:
                self.data.type = text_type
        return self

    @classmethod
    def from_text(cls, text: str, sub_type: Optional[str] = None) -> TextBlock:
        block_type = f"text:{sub_type}" if sub_type else "text"
        return TextBlock(block_type=block_type, data=TextData(text=text))
