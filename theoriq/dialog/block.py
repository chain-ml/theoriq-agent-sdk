from __future__ import annotations

import json
from typing import Annotated, Any, Callable, Generic, Optional, Sequence, Type, TypeVar, Union

from pydantic import BaseModel, Field
from pydantic.alias_generators import to_camel


class BaseTheoriqModel(BaseModel):

    class Config:
        populate_by_name = True
        alias_generator = to_camel

    @staticmethod
    def _set_dump_defaults(kwargs):
        """Set default serialization options"""
        kwargs.setdefault("by_alias", True)
        kwargs.setdefault("exclude_none", True)
        kwargs.setdefault("exclude_defaults", True)
        kwargs.setdefault("exclude_unset", True)
        return kwargs

    def model_dump_json(self, **kwargs) -> str:
        """Override to ensure proper JSON serialization"""
        return super().model_dump_json(**BaseTheoriqModel._set_dump_defaults(kwargs))

    def model_dump(self, **kwargs) -> dict[str, Any]:
        """Override to ensure proper JSON serialization"""
        return super().model_dump(**BaseTheoriqModel._set_dump_defaults(kwargs))


class BaseData(BaseTheoriqModel):
    """
    Base class for data items in blocks.
    This class can be extended to create specific data types.
    """

    def to_str(self) -> str:
        """Returns a human-friendly description of the object for LLM usage."""
        lines = [f"{self.__class__.__name__}:"]
        for field_name, field in self.model_fields.items():
            value = getattr(self, field_name)
            if isinstance(value, BaseData):
                nested = value.to_str().replace("\n", "\n  ")
                description = field.description
                desc = f" ({description})" if description else ""
                lines.append(f"- {field_name}{desc}: \n  {nested}")
            elif isinstance(value, list):
                lines.append(f"- {field_name}:")
                for item in value:
                    if isinstance(item, BaseData):
                        nested = item.to_str().replace("\n", "\n    ")
                        lines.append(f"  - {nested}")
                    else:
                        lines.append(f"  - {repr(item)}")
            else:
                description = field.description
                desc = f" ({description})" if description else ""
                lines.append(f"- {field_name}{desc}: {repr(value)}")
        return "\n".join(lines)

    def __str__(self) -> str:
        """
        Returns a string representation of the BaseData instance.
        """
        return self.model_dump_json(by_alias=True, exclude_none=True)


T_Data = TypeVar("T_Data", bound=Union[BaseData, dict[str, Any]])
T_Type = TypeVar("T_Type", bound=str)


class BlockBase(BaseTheoriqModel, Generic[T_Data, T_Type]):
    ref: Annotated[Optional[str], Field(default=None)] = None
    key: Annotated[Optional[str], Field(default=None)] = None
    block_type: Annotated[T_Type, Field(alias="type")]
    data: T_Data

    class Config:
        populate_by_name = True

    @staticmethod
    def sub_type(block_type: T_Type) -> Optional[str]:
        """
        Extracts the subtype from a block type string.

        Args:
            block_type (str): The block type string (e.g., "custom:subtype").

        Returns:
            str: The subtype part of the block type.
        """
        parts = block_type.split(":", 1)
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

    def to_str(self) -> str:
        if isinstance(self.data, BaseData):
            return self.data.to_str()
        return json.dumps(self.data, indent=2)


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


BlockBasePredicate = Callable[[BlockBase], bool]


def AllBlocks(_: BlockBase) -> bool:
    """Predicate that matches all blocks."""
    return True


def BlockOfTypes(block_types: Sequence[Type[BlockBase]]) -> BlockBasePredicate:
    def predicate(block: BlockBase) -> bool:
        return any(isinstance(block, block_type) for block_type in block_types)

    return predicate


def BlockOfType(block_type: T_Type) -> BlockBasePredicate:
    def predicate(block: BlockBase) -> bool:
        return block.is_of_type(block_type)

    return predicate
