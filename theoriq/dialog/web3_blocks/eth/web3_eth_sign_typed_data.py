from __future__ import annotations

import json
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel

from ...web3 import Web3Item
from .web3_eth_base import Web3EthBaseBlock


# Types
class DomainType(BaseModel):
    name: str
    version: str
    chainId: int
    salt: str
    verifyingContract: str


EIP712Type = Literal["uint256", "int256", "bool", "address", "bytes32", "bytes", "string"]
EIP712ArrayType = Literal["uint256[]", "int256[]", "bool[]", "address[]", "bytes32[]", "bytes[]", "string[]"]


class Web3EthTypedDataMessageType(BaseModel):
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

    @classmethod
    def validate_args(cls, args: dict) -> None:
        """
        Validates the data for the Web3EthSignTypedDataBlock.

        Args:
            data (dict): The data to validate.
        """
        super().validate_args(args)
        try:
            Web3EthTypedDataMessageType(**args)
        except Exception as e:
            raise ValueError(f"{cls.__name__}: Invalid data type") from e

        if args["domain"]["salt"].startswith("0x") and len(args["domain"]["salt"]) != 66:
            raise ValueError(f"{cls.__name__}: Invalid salt. Must be a 66 character hex string starting with 0x")

        if args["domain"]["verifyingContract"].startswith("0x") and len(args["domain"]["verifyingContract"]) != 42:
            raise ValueError(f"{cls.__name__}: Invalid verifyingContract")

        if "EIP712Domain" not in args["types"]:
            raise ValueError(f"{cls.__name__}: Invalid types")

        if args["primaryType"] not in args["types"]:
            raise ValueError(f"{cls.__name__}: Invalid primaryType")


class Web3EthSignTypedDataBlock(Web3EthBaseBlock):
    """
    A class representing a block of web3 eth sign typed data items. Inherits from ItemBlock with Web3EthSignTypedDataItem as the generic type.
    """

    def __init__(self, data: Dict[str, Any], key: Optional[str] = None, reference: Optional[str] = None) -> None:
        """
        Initializes a Web3EthSignTypedDataBlock instance.

        Args:
            data (Dict[str, Any]): The data to be signed.
        """
        super().__init__(
            item=Web3Item(
                chain_id=self.get_web3_chain_id(),
                method=self.get_web3_method(),
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
    def from_dict(cls, data: Dict[str, Any], block_type: str) -> Web3EthSignTypedDataBlock:
        """
        Creates an instance of Web3EthSignTypedDataBlock from a dictionary.

        Args:
            data (Dict[str, Any]): The dictionary containing the data to be signed and their types.

        Returns:
            Web3EthSignTypedDataBlock: A new instance of Web3EthSignTypedDataBlock initialized with the provided data.
        """
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        return cls(data=data["data"])

    @staticmethod
    def get_web3_method() -> str:
        """
        Returns the web3 method for the Web3EthSignTypedDataBlock.

        Returns:
            str: The web3 method for the Web3EthSignTypedDataBlock.
        """
        return "eth_signTypedData_v4"
