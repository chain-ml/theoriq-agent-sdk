"""
schemas.py

This module contains the schemas used by the Theoriq endpoint.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, Sequence, Type, TypeVar, Union

from typing_extensions import Self


class BaseData(ABC):
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def to_str(self) -> str:
        pass

    def __str__(self) -> str:
        return str(self.to_dict())  # default str representation of BaseData, to be overwritten by subclasses


T_Data = TypeVar("T_Data", bound=Union[BaseData, Sequence[BaseData]])


class ItemBlock(Generic[T_Data]):
    """
    ItemBlock is a generic class that encapsulates a block of data, identified by a
    specific block type. It can hold any data type (T_Data), and includes optional
    key and reference attributes.
    """

    def __init__(
        self, *, block_type: str, data: T_Data, key: Optional[str] = None, reference: Optional[str] = None
    ) -> None:
        """
        Initializes the ItemBlock instance with block type, data, key, and reference.

        Args:
            block_type (str): A string representing the type of the block.
            data (T_Data): The data encapsulated in the block.
            key (Optional[str]): An optional key to uniquely identify the block.
            reference (Optional[str]): An optional reference to external data.
        """
        self._block_type = block_type
        self.data = data
        self.key = key
        self.reference = reference

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the ItemBlock and its contents into a dictionary format.

        Returns:
            Dict[str, Any]: A dictionary representation of the block's data.
        """
        result: Dict[str, Any] = {"type": self._block_type}

        # Check if data is a BaseData instance and convert it to a dictionary
        if isinstance(self.data, BaseData):
            result["data"] = self.data.to_dict()

        # If data is a sequence, create a dictionary for each item
        elif isinstance(self.data, Sequence):
            result["data"] = {"items": [d.to_dict() for d in self.data]}

        # Include optional key and reference if they exist
        if self.key is not None:
            result["key"] = self.key
        if self.reference is not None:
            result["ref"] = self.reference
        return result

    def to_str(self, title: Optional[str] = None) -> str:
        data = self.data if isinstance(self.data, Sequence) else [self.data]
        result = [d.to_str() for d in data]
        if title:
            result.insert(0, title)
        return "\n".join(result)

    @classmethod
    def from_dict(
        cls, data: dict, block_type: str, block_key: Optional[str] = None, block_ref: Optional[str] = None
    ) -> Self:
        """
        Abstract method to create an instance of ItemBlock from a dictionary.

        Args:
            data (dict): The data dictionary from which the block is created.
            block_type (str): The block type of the block being created.
            block_key (Optional[str]): The key of the block being created.
            block_ref (Optional[str]): The reference of the block being created.

        Raises:
            NotImplementedError: This method should be implemented in a subclass.
        """
        raise NotImplementedError

    @staticmethod
    def is_valid(block_type: str) -> bool:
        """
        Abstract method to validate whether a given block_type is valid.

        Args:
            block_type (str): The block type to be validated.

        Raises:
            NotImplementedError: This method should be implemented in a subclass.
        """
        raise NotImplementedError

    @staticmethod
    def block_type() -> str:
        """
        Abstract method to return the block type string identifier.

        Raises:
            NotImplementedError: This method should be implemented in a subclass.
        """
        raise NotImplementedError

    @staticmethod
    def raise_if_not_valid(*, block_type: str, expected: str) -> None:
        """
        Validates if the block type matches the expected format. Raises a ValueError
        if not valid.

        Args:
            block_type (str): The block type to validate.
            expected (str): The expected block type or its subtype.

        Raises:
            ValueError: If the block type does not match the expected format.
        """
        if not block_type.startswith(expected):
            raise ValueError(f"Data type must be subtype of {expected}, not {block_type}")

    @staticmethod
    def sub_type(bloc_type: str) -> str:
        """
        Extracts the subtype from a block type string.

        Args:
            bloc_type (str): The block type string (e.g., "custom:subtype").

        Returns:
            str: The subtype part of the block type.
        """
        parts = bloc_type.split(":", 1)
        return parts[1] if len(parts) > 1 else ""

    @staticmethod
    def root_type(bloc_type: str) -> str:
        """
        Extracts the root type from a block type string.

        Args:
            bloc_type (str): The block type string (e.g., "custom:subtype").

        Returns:
            str: The root type of the block (e.g., "custom").
        """
        return bloc_type.split(":", 1)[0]

    def __str__(self) -> str:
        """
        String representation of the ItemBlock.

        Returns:
            str: A string representing the block type and data.
        """
        result = f"block_type={self._block_type}, data={self.data}"
        if self.key is not None:
            result += f", key={self.key}"
        if self.reference is not None:
            result += f" reference={self.reference}"
        return result


def filter_blocks(blocks: Sequence[ItemBlock], block_type: Type[ItemBlock]) -> Sequence[ItemBlock]:
    """
    Filters a sequence of ItemBlocks based on a given block type.

    Args:
        blocks (Sequence[ItemBlock]): A sequence of ItemBlocks to filter.
        block_type (Type[ItemBlock]): The block type to filter by.

    Returns:
        Sequence[ItemBlock]: A filtered list of ItemBlocks that match the block type.
    """
    return list(filter(lambda x: block_type.is_valid(x.block_type()), blocks))
