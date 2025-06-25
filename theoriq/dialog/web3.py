from __future__ import annotations

from typing import Any, Dict, Generic, Optional, Type, TypeVar

from .item_block import ItemBlock

T = TypeVar("T")


class Web3ItemBlock(ItemBlock, Generic[T]):
    """
    A class representing a router for web3 blocks. This acts as a factory that creates
    the appropriate specific web3 block type based on the block_type. Specific web3
    block types should inherit from this class.
    """

    _registry: Dict[str, Type[Web3ItemBlock]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        Web3ItemBlock._registry[cls.block_type()] = cls

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], block_type: str, block_key: Optional[str] = None, block_ref: Optional[str] = None
    ) -> Web3ItemBlock:
        """
        Router method that creates the appropriate specific web3 block type based on block_type.

        Args:
            data (Dict[str, Any]): The dictionary containing the web3 item data.
            block_type (str): The type of the block (e.g., "web3:proposedTx", "web3:signedTx").
            block_key (Optional[str]): An optional key to uniquely identify the block.
            block_ref (Optional[str]): An optional reference to external data.

        Returns:
            Web3ItemBlock: The appropriate specific web3 block instance.
        """
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())

        block_class = cls._registry.get(block_type)
        if block_class is None:
            raise ValueError(f"Invalid item type {block_type}, expected one of {', '.join(cls._registry.keys())}")

        return block_class.from_dict(data, block_type, block_key, block_ref)

    @staticmethod
    def block_type() -> str:
        """
        Returns the block type for Web3ItemBlock.

        Returns:
            str: The string 'web3', representing the block type.
        """
        return "web3"

    @staticmethod
    def is_valid(block_type: str) -> bool:
        """
        Checks if the provided block type is valid for a Web3ItemBlock.

        Args:
            block_type (str): The block type to validate.

        Returns:
            bool: True if the block type is valid, False otherwise.
        """
        return block_type.startswith(Web3ItemBlock.block_type())
