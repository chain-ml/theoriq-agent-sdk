from typing import Optional

from ...web3 import Web3Item, Web3ItemBlock


class Web3EthBaseBlock(Web3ItemBlock):
    """
    A class representing a base block for web3 eth operations.
    """

    def __init__(
        self,
        item: Web3Item,
        key: Optional[str] = None,
        reference: Optional[str] = None,
    ) -> None:
        """
        Initializes a Web3EthBaseBlock instance.

        Args:
            item (Web3Item): The item to be used for the operation.
        """
        super().__init__(
            item=item,
            key=key,
            reference=reference,
        )

    @staticmethod
    def get_web3_chain_id() -> int:
        return 1

    @staticmethod
    def get_web3_method() -> str:
        raise NotImplementedError("Subclasses must implement this method")
