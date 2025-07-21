from __future__ import annotations

from typing import Annotated, Any, Dict

from pydantic import Field, field_validator, model_validator

from . import BlockBase
from .dialog import BaseData


class CustomData(BaseData):
    data: Dict[str, Any]
    custom_type: str


class CustomBlock(BlockBase[CustomData, Annotated[str, Field(pattern="custom:(.*)?")]]):
    """
    CustomItemBlock is a specialized ItemBlock that wraps around CustomData.
    It provides additional functionality to handle and validate custom block types.
    """

    @field_validator("block_type")
    def validate_block_type(cls, v):
        if not v.startswith("custom"):
            raise ValueError('CustomBlock block_type must start with "custom"')
        return v

    @model_validator(mode="after")
    def set_type_from_block_type(self):
        if self.data and not self.data.custom_type:
            custom_type = self.sub_type(self.block_type)
            if custom_type:
                self.data.custom_type = custom_type
        return self
