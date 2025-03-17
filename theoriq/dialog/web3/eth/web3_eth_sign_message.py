from __future__ import annotations

from typing import Any, Dict, Optional

from .. import Web3Item
from .web3_eth_base import Web3EthBaseBlock


class Web3EthSignMessageItem(Web3Item):
    """
    A class representing a web3 eth sign message item.
    """

    def __str__(self):
        """
        Converts the web3EthPersonalSignItem instance into a string.

        Returns:
            str: A string representing the web3EthSignMessageItem.
        """
        return f"Web3EthSignMessageItem(chain_id={self.chain_id}, message={self.args.message})"


class Web3EthSignMessageBlock(Web3EthBaseBlock):
    """
    A class representing a block of web3 eth sign message items. Inherits from Web3ItemBlock.
    """

    def __init__(self, message: str, key: Optional[str] = None, reference: Optional[str] = None) -> None:
        """
        Initializes a Web3EthSignMessageBlock instance.

        Args:
            message (str): The message to be signed.
        """
        super().__init__(
            item=Web3Item(
                chain_id=self.__class__.getWeb3ChainId(),
                method=self.__class__.getWeb3Method(),
                args={"message": message},
            ),
            key=key,
            reference=reference,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any], block_type: str) -> Web3EthSignMessageBlock:
        """
        Creates an instance of Web3EthSignMessageBlock from a dictionary.

        Args:
            data (Dict[str, Any]): The dictionary containing the web3 item.
            block_type (str): The type of the block.

        Returns:
            Web3EthSignMessageBlock: A new instance of Web3EthSignMessageBlock initialized with the provided data.
        """
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        return cls(message=data["message"])

    @staticmethod
    def getWeb3Method() -> str:
        return "eth_sign"
