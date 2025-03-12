from __future__ import annotations

import json
from typing import Any, Dict, Optional

from ..item_block import BaseData, ItemBlock


class Web3Item(BaseData):
    """
    A class representing a Base Web3 item. Inherits from BaseData.
    """

    def __init__(self, *, chain_id: int, method: str, args: Dict[str, Any]) -> None:
        """
        Initializes a Web3Item instance.

        Args:
            chain_id (int): The chain_id that this web3 item is related to.
            method (str): The method that this web3Item will execute.
            args (List[str]): The arguments that this web3Item will execute with.
        """
        self.chain_id = chain_id
        self.method = method
        self.args = args

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the web3Item instance into a dictionary.

        Returns:
            Dict[str, Any]: A dictionary that contains the chain_id, method, and args.
        """
        return {"chain_id": self.chain_id, "method": self.method, "args": self.args}

    def to_str(self) -> str:
        """
        Converts the web3Item instance into a string.

        Returns:
            str: A string representing the web3Item.
        """
        args = json.dumps(self.args)
        # skip ` in the args str
        args = args.replace("`", "\\`")
        result = [f"```{self.chain_id}", self.method, args, "```"]
        return "\n".join(result)

    def __str__(self):
        """
        Converts the web3Item instance into a string.

        Returns:
            str: A string representing the web3Item.
        """
        return f"Web3Item(chain_id={self.chain_id}, method={self.method}, args={json.dumps(self.args)})"


class Web3ItemBlock(ItemBlock[Web3Item]):
    """
    A class representing a block of web3 items. Inherits from ItemBlock with Web3Item as the generic type.
    """

    def __init__(
        self,
        *,
        chain_id: int,
        method: str,
        args: Dict[str, Any],
        sub_type: str | None = None,
        key: Optional[str] = None,
        reference: Optional[str] = None,
    ) -> None:
        """
        Initializes a Web3ItemBlock instance.

        Args:
            chain_id (int): The chain_id that this web3 item is related to.
            method (str): The method that this web3Item will execute.
            args (Dict[str, Any]): The arguments that this web3Item will execute with.
        """

        block_type = f"{Web3ItemBlock.block_type()}:{sub_type}" if sub_type else Web3ItemBlock.block_type()
        super().__init__(
            block_type=block_type,
            data=Web3Item(chain_id=chain_id, method=method, args=args),
            key=key,
            reference=reference,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any], block_type: str) -> Web3ItemBlock:
        """
        Creates an instance of Web3ItemBlock from a dictionary.

        Args:
            data (Dict[str, Any]): The dictionary containing the web3 item.
            block_type (str): The type of the block.

        Returns:
            Web3ItemBlock: A new instance of Web3ItemBlock initialized with the provided data.
        """
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        return cls(chain_id=data["chain_id"], method=data["method"], args=data["args"])

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
        return block_type == Web3ItemBlock.block_type()
