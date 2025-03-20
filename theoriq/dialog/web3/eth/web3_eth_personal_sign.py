from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel

from .. import Web3Item
from .web3_eth_base import Web3EthBaseBlock


class Web3EthPersonalSignArgs(BaseModel):
    message: str


class Web3EthPersonalSignItem(Web3Item):
    """
    A class representing a web3 eth personal sign item.
    """

    def __init__(
        self,
        chain_id: int,
        method: str,
        args: Dict[str, Any],
        key: Optional[str] = None,
        reference: Optional[str] = None,
    ) -> None:
        """
        Initializes a Web3EthPersonalSignItem instance.

        Args:
            message (str): The message to be signed.
            key (Optional[str]): The key to be used for the signature.
            reference (Optional[str]): The reference to the item.
        """
        super().__init__(
            chain_id=chain_id,
            method=method,
            args=Web3EthPersonalSignArgs(message=args["message"]).dict(),
        )
        self.key = key
        self.reference = reference

    def __str__(self):
        """
        Converts the web3EthPersonalSignItem instance into a string.

        Returns:
            str: A string representing the web3EthPersonalSignItem.
        """
        return f"Web3EthPersonalSignItem(chain_id={self.chain_id}, message={self.args.message})"

    @classmethod
    def validate_args(cls, args: Dict[str, Any]) -> None:
        super().validate_args(args)
        if "message" not in args:
            raise ValueError(f"{cls.__name__}: message must be a key in the args dictionary")
        if not isinstance(args["message"], str):
            raise ValueError(f"{cls.__name__}: message must be a string")


class Web3EthPersonalSignBlock(Web3EthBaseBlock):
    """
    A class representing a block of web3 eth personal sign items. Inherits from Web3ItemBlock.
    """

    def __init__(self, message: str, key: Optional[str] = None, reference: Optional[str] = None) -> None:
        """
        Initializes a Web3EthPersonalSignBlock instance.

        Args:
            message (str): The message to be signed.
        """
        super().__init__(
            item=Web3Item(
                chain_id=self.__class__.get_web3_chain_id(),
                method=self.__class__.get_web3_method(),
                args={"message": message},
            ),
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
        return cls(message=data["message"])

    @staticmethod
    def get_web3_method() -> str:
        return "personal_sign"
