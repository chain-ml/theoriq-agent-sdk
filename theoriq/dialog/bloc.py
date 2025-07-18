from __future__ import annotations

from typing import TypeVar, Union, Any, Generic, Annotated, Optional, Sequence, Type

from pydantic import BaseModel, Field

T_Data = TypeVar("T_Data", bound=Union[BaseModel, dict[str, Any]])
T_Type = TypeVar("T_Type", bound=str)


class BlockBase(BaseModel, Generic[T_Data, T_Type]):
    ref: Annotated[Optional[str], Field(default=None)] = None
    key: Annotated[Optional[str], Field(default=None)] = None
    block_type: Annotated[T_Type, Field(alias="type")]
    data: T_Data

    class Config:
        populate_by_name = True

    def model_dump_json(self, **kwargs):
        """Override to ensure proper JSON serialization"""
        # Set default serialization options
        kwargs.setdefault("by_alias", True)
        kwargs.setdefault("exclude_none", True)
        kwargs.setdefault("exclude_defaults", True)
        kwargs.setdefault("exclude_unset", True)
        return super().model_dump_json(**kwargs)

    @staticmethod
    def sub_type(bloc_type: T_Type) -> Optional[str]:
        """
        Extracts the subtype from a block type string.

        Args:
            bloc_type (str): The block type string (e.g., "custom:subtype").

        Returns:
            str: The subtype part of the block type.
        """
        parts = bloc_type.split(":", 1)
        return parts[1] if len(parts) > 1 else None

    def is_of_type(self, block_type: T_Type) -> bool:
        """
        Checks if the block is of a specific type.

        Args:
            block_type (T_Type): The block type to check against.

        Returns:
            bool: True if the block is of the specified type, False otherwise.
        """
        sub_type = BlockBase.sub_type(block_type)
        if sub_type:
            return self.block_type == block_type
        return self.block_type.startswith(block_type)


def filter_blocks(blocks: Sequence[BlockBase], block_type: Type[BlockBase]) -> Sequence[BlockBase]:
    """
    Filters a sequence of BlockBase based on a given block type.

    Args:
        blocks (Sequence[BlockBase]): A sequence of BlockBase to filter.
        block_type (T_Type): The block type to filter by.

    Returns:
        Sequence[BlockBase]: A filtered list of BlockBase that match the block type.
    """
    return list(filter(lambda x: isinstance(x, block_type), blocks))
