from __future__ import annotations

import abc
from abc import ABC
from typing import Any, Dict, Optional

from .schemas import BaseData, ItemBlock


class CustomData(BaseData):

    def __init__(self, data: Dict[str, Any], custom_type: str) -> None:
        self._data = data
        self._custom_type = custom_type

    def custom_type(self) -> str:
        return self._custom_type

    def to_dict(self) -> Dict[str, Any]:
        return self._data


class CustomItemBlock(ItemBlock[CustomData]):
    """ """

    def __init__(self, data: CustomData, key: Optional[str] = None, reference: Optional[str] = None) -> None:
        """
        Initializes a CustomItemBlock instance.
        """
        block_type = f"custom:{data.custom_type()}"
        super().__init__(bloc_type=block_type, data=data, key=key, reference=reference)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], block_type: str) -> CustomItemBlock:
        """
        Creates an instance of CustomItemBlock from a dictionary.

        Args:
            data (Dict[str, Any]): The dictionary containing the metrics.
            block_type (str): The type of the block.

        Returns:
            CustomItemBlock: A new instance of CustomItemBlock initialized with the provided data.
        """
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        custom_type = block_type.split(":", 1)[1]
        return cls(data=CustomData(data, custom_type=custom_type))

    @staticmethod
    def block_type() -> str:
        """
        Returns the block type for MetricsItemBlock.

        Returns:
            str: The string 'custom', representing the block type.
        """
        return "custom"

    @staticmethod
    def is_valid(block_type: str) -> bool:
        """
        Checks if the provided block type is valid for a CustomItemBlock.

        Args:
            block_type (str): The block type to validate.

        Returns:
            bool: True if the block type is valid, False otherwise.
        """
        return block_type.startswith("custom:")
