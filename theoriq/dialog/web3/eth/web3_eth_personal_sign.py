from __future__ import annotations

from typing import Any, Dict, Optional

from ..web3_base import Web3Item, Web3ItemBlock


class Web3EthPersonalSignItem(Web3Item):
    """
    A class representing a web3 eth personal sign item.
    """

    def __str__(self):
        """
        Converts the web3EthPersonalSignItem instance into a string.

        Returns:
            str: A string representing the web3EthPersonalSignItem.
        """
        return f"Web3EthPersonalSignItem(chain_id={self.chain_id}, message={self.message})"


class Web3EthPersonalSignBlock(Web3ItemBlock):
    """
    A class representing a block of web3 eth personal sign items. Inherits from ItemBlock with Web3EthPersonalSignItem as the generic type.
    """

    ETH_METHOD_PERSONAL_SIGN = "eth_personal_sign"

    def __init__(self, chain_id: int, message: str, key: Optional[str] = None, reference: Optional[str] = None) -> None:
        """
        Initializes a Web3ItemBlock instance.

        Args:
            chain_id (int): The chain_id that this web3 item is related to.
            message (str): The message to be signed.
        """
        super().__init__(
            chain_id=chain_id,
            method=Web3EthPersonalSignBlock.ETH_METHOD_PERSONAL_SIGN,
            args={"message": message},
            key=key,
            reference=reference,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any], block_type: str) -> Web3EthPersonalSignBlock:
        """
        Creates an instance of Web3EthPersonalSignBlock from a dictionary.

        Args:
            data (Dict[str, Any]): The dictionary containing the web3 item.
            block_type (str): The type of the block.

        Returns:
            Web3EthPersonalSignBlock: A new instance of Web3EthPersonalSignBlock initialized with the provided data.
        """
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        return cls(chain_id=data["chain_id"], message=data["message"])
