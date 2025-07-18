from __future__ import annotations

from typing import Annotated, Optional

from pydantic import Field, field_validator, model_validator

from .block import BaseData, BlockBase


class DataItem(BaseData):
    data: str
    type: Optional[str]

    def to_str(self) -> str:
        if self.type is None:
            return self.data

        result = [f"```{self.type}", self.data, "```"]
        return "\n".join(result)

    def __str__(self) -> str:
        """
        Returns a string representation of the DataItem instance.

        Returns:
            str: A string representing the DataItem.
        """
        data = self.data if len(self.data) < 50 else f"{self.data[:50]}..."
        return f"DataItem(data={data}, type={self.type})"


class DataBlock(BlockBase[DataItem, Annotated[str, Field(pattern="data(:.*)?")]]):
    @field_validator("block_type")
    def validate_block_type(cls, v):
        if not v.startswith("data"):
            raise ValueError('DataBlock block_type must start with "data"')
        return v

    @model_validator(mode="after")
    def set_data_type_from_block_type(self):
        if self.data and not self.data.type:
            data_type = self.sub_type(self.block_type)
            if data_type:
                self.data.type = data_type
        return self

    @classmethod
    def from_data(cls, data: str, sub_type: Optional[str] = None) -> DataBlock:
        block_type = f"data:{sub_type}" if sub_type else "data"
        return DataBlock(block_type=block_type, data=DataItem(data=data, type=sub_type))
