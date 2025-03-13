from __future__ import annotations

import json
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union

from ..web3_base import Web3Item
from .web3_eth_base import Web3EthBaseBlock


# Types
class DomainType(TypedDict):
    name: str
    version: str
    chainId: int
    salt: str
    verifyingContract: str


EIP712Type = Literal["uint256", "int256", "bool", "address", "bytes32", "bytes", "string"]

EIP712ArrayType = Literal["uint256[]", "int256[]", "bool[]", "address[]", "bytes32[]", "bytes[]", "string[]"]


class Web3EthTypedDataMessageType(TypedDict):
    domain: DomainType
    types: Dict[str, List[Dict[str, Union[str, EIP712Type, EIP712ArrayType]]]]
    primaryType: str
    message: Dict[str, object]


class Web3EthSignTypedDataItem(Web3Item):
    """
    A class representing a web3 eth sign typed data item.
    """

    def __str__(self):
        """
        Converts the web3EthSignTypedDataItem instance into a string.

        Returns:
            str: A string representing the web3EthSignTypedDataItem.
        """
        data = json.dumps(self.args)
        return f"Web3EthSignTypedDataItem(chain_id={self.chain_id}, data={data})"


class Web3EthSignTypedDataBlock(Web3EthBaseBlock):
    """
    A class representing a block of web3 eth sign typed data items. Inherits from ItemBlock with Web3EthSignTypedDataItem as the generic type.
    """

    def __init__(
        self, data: Web3EthTypedDataMessageType, key: Optional[str] = None, reference: Optional[str] = None
    ) -> None:
        """
        Initializes a Web3EthSignTypedDataBlock instance.

        Args:
            data (Web3EthTypedDataMessageType): The data to be signed.
        """
        self.__class__.raiseIfInvalidDataType(dict(data))
        super().__init__(
            method=self.__class__.getWeb3Method(),
            args={
                "domain": data["domain"],
                "types": data["types"],
                "primaryType": data["primaryType"],
                "message": data["message"],
            },
            BlockItem=Web3EthSignTypedDataItem,
            key=key,
            reference=reference,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any], block_type: str) -> Web3EthSignTypedDataBlock:
        """
        Creates an instance of Web3EthSignTypedDataBlock from a dictionary.

        Args:
            data (Web3EthTypedDataMessageType): The dictionary containing the Web3EthTypedDataMessageType data.

        Returns:
            Web3EthSignTypedDataBlock: A new instance of Web3EthSignTypedDataBlock initialized with the provided data.
        """
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        cls.raiseIfInvalidDataType(data)
        return cls(data=data["data"])

    @staticmethod
    def getWeb3Method() -> str:
        """
        Returns the web3 method for the Web3EthSignTypedDataBlock.

        Returns:
            str: The web3 method for the Web3EthSignTypedDataBlock.
        """
        return "eth_signTypedData_v4"

    @staticmethod
    def raiseIfInvalidDataType(data: dict) -> None:
        """
        Validates the data for the Web3EthSignTypedDataBlock.

        Args:
            data (dict): The data to validate.
        """
        if data["domain"]["salt"].startswith("0x") and len(data["domain"]["salt"]) != 66:
            raise ValueError("Invalid salt")

        print(data["domain"]["verifyingContract"])
        if data["domain"]["verifyingContract"].startswith("0x") and len(data["domain"]["verifyingContract"]) != 42:
            raise ValueError("Invalid verifyingContract")

        if "EIP712Domain" not in data["types"]:
            raise ValueError("Invalid types")

        if data["primaryType"] not in data["types"]:
            raise ValueError("Invalid primaryType")
