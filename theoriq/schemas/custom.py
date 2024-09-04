from __future__ import annotations

import abc
from abc import ABC
from typing import Any, Dict, Optional

from .schemas import BaseData, ItemBlock


class CustomData(BaseData, ABC):
    def __init__(self, data: Any) -> None:
        self._data = data

    @staticmethod
    @abc.abstractmethod
    def from_dict(values: Dict[str, Any]) -> CustomData:
        pass

    @staticmethod
    @abc.abstractmethod
    def type() -> str:
        pass

    @abc.abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass


class CustomItemBlock(ItemBlock[CustomData]):
    """ """

    def __init__(self, data: CustomData, key: Optional[str] = None, reference: Optional[str] = None) -> None:
        """
        Initializes a CustomItemBlock instance.
        """
        block_type = f"custom:{data.type()}"
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
        return cls(data=CustomData.from_dict(data))

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
