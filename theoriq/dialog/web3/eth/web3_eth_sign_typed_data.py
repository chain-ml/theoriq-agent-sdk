from __future__ import annotations

from typing import Any, Dict, Optional

from .. import Web3Item
from .web3_eth_base import Web3EthBaseBlock


class Web3EthSignTypedDataItem(Web3Item):
    """
    A class representing a web3 eth sign typed data item.
    """

    def __str__(self):
        """
        Converts the web3EthPersonalSignItem instance into a string.

        Returns:
            str: A string representing the web3EthPersonalSignItem.
        """
        return f"Web3EthPersonalSignItem(chain_id={self.chain_id}, message={self.message})"


class Web3EthSignTypedDataBlock(Web3EthBaseBlock):
    """
    A class representing a block of web3 eth personal sign items. Inherits from ItemBlock with Web3EthPersonalSignItem as the generic type.
    """

    def __init__(self, data: Dict[str, Any], key: Optional[str] = None, reference: Optional[str] = None) -> None:
        """
        Initializes a Web3ItemBlock instance.

        Args:
            message (str): The message to be signed.
        """
        self.__class__.raiseIfInvalidDataType(dict(data))

        super().__init__(
            item=Web3Item(
                chain_id=self.__class__.getWeb3ChainId(),
                method=self.__class__.getWeb3Method(),
                args={
                    "domain": data["domain"],
                    "types": data["types"],
                    "primaryType": data["primaryType"],
                    "message": data["message"],
                },
            ),
            key=key,
            reference=reference,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any], block_type: str, block_key: Optional[str] = None, block_ref: Optional[str] = None) -> Web3EthSignTypedDataBlock:
        """
        Creates an instance of Web3EthPersonalSignBlock from a dictionary.

        Args:
            data (Dict[str, Any]): The dictionary containing the web3 item.
            block_type (str): The type of the block.

        Returns:
            Web3EthPersonalSignBlock: A new instance of Web3EthPersonalSignBlock initialized with the provided data.
        """
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        cls.raiseIfInvalidDataType(data)
        return cls(data=data["data"], key=block_key, reference=block_ref)

    @staticmethod
    def getWeb3Method() -> str:
        return "eth_signTypedData_v4"
