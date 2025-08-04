from __future__ import annotations

from typing import Annotated, Any, Dict, Optional

from pydantic import Field, field_validator, model_serializer, model_validator

from .block import BaseData, BlockBase


class CustomData(BaseData):
    data: Dict[str, Any]
    custom_type: Optional[str] = None

    @model_serializer
    def serialize_model(self) -> dict[str, Any]:
        """Override to ensure proper JSON serialization"""
        return self.data

    @model_validator(mode="before")
    def validate_data(cls, v):
        new_value = {"data": v}
        return new_value


class CustomBlock(BlockBase[CustomData, Annotated[str, Field(pattern="custom(:.*)?")]]):
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
