from __future__ import annotations

from typing import Annotated, Any, Dict, Optional

from pydantic import Field, field_validator, model_validator

from .block import BaseData, BlockBase



class CustomBlock(BlockBase[Dict[str, Any], Annotated[str, Field(pattern="custom:(.*)?")]]):
    """
    CustomItemBlock is a specialized ItemBlock that wraps around CustomData.
    It provides additional functionality to handle and validate custom block types.
    """

    @field_validator("block_type")
    def validate_block_type(cls, v):
        if not v.startswith("custom"):
            raise ValueError('CustomBlock block_type must start with "custom"')
        return v


    @classmethod
    def from_data(cls, data: Dict[str, Any], custom_type: str) -> CustomBlock:
        """
        Creates a CustomBlock from the provided data and custom type.

        Args:
            data (Dict[str, Any]): The custom data to be wrapped.
            custom_type (str): The type of the custom block.

        Returns:
            CustomBlock: An instance of CustomBlock with the provided data and type.
        """
        return cls(block_type=f"custom:{custom_type}", data=CustomData(data=data, custom_type=custom_type))
