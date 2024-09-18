from __future__ import annotations

import json
from typing import Any, Dict, Optional

from .schemas import BaseData, ItemBlock


class CustomData(BaseData):
    """
    CustomData is a specialized data wrapper that stores a dictionary of arbitrary data
    along with an associated custom type. It extends the functionality of BaseData by
    allowing the storage and retrieval of this custom type.
    """

    def __init__(self, data: Dict[str, Any], custom_type: str) -> None:
        """
        Initializes the CustomData instance.

        Args:
            data (Dict[str, Any]): The dictionary containing the data.
            custom_type (str): A string representing the type of the custom data.
        """
        self._data = data
        self._custom_type = custom_type

    def custom_type(self) -> str:
        """
        Returns the custom type of the data.

        Returns:
            str: The custom type of the data.
        """
        return self._custom_type

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the internal data into a dictionary.

        Returns:
            Dict[str, Any]: The dictionary representation of the internal data.
        """
        return self._data

    def to_str(self) -> str:
        return json.dumps(self._data)


class CustomItemBlock(ItemBlock[CustomData]):
    """
    CustomItemBlock is a specialized ItemBlock that wraps around CustomData.
    It provides additional functionality to handle and validate custom block types.
    """

    def __init__(self, data: CustomData, key: Optional[str] = None, reference: Optional[str] = None) -> None:
        """
        Initializes a CustomItemBlock instance.

        Args:
            data (CustomData): The custom data object encapsulated by this block.
            key (Optional[str]): An optional key associated with the block.
            reference (Optional[str]): An optional reference ID associated with the block.
        """
        block_type = f"custom:{data.custom_type()}"
        super().__init__(block_type=block_type, data=data, key=key, reference=reference)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], block_type: str) -> CustomItemBlock:
        """
        Creates an instance of CustomItemBlock from a dictionary.

        Args:
            data (Dict[str, Any]): The dictionary containing the data.
            block_type (str): The type of the block (must be a 'custom' block).

        Returns:
            CustomItemBlock: A new instance of CustomItemBlock initialized with the provided data.

        Raises:
            ValueError: If the block_type is not valid for CustomItemBlock.
        """
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        custom_type = block_type.split(":", 1)[1]
        return cls(data=CustomData(data, custom_type=custom_type))

    @staticmethod
    def block_type() -> str:
        """
        Returns the block type identifier for CustomItemBlock.

        Returns:
            str: The block type identifier ('custom').
        """
        return "custom"

    @staticmethod
    def is_valid(block_type: str) -> bool:
        """
        Checks if the provided block type is valid for a CustomItemBlock.

        Args:
            block_type (str): The block type to validate.

        Returns:
            bool: True if the block type starts with 'custom:', False otherwise.
        """
        return block_type.startswith("custom:")
