from typing import Any, Dict, Optional

from ..web3_base import Web3Item, Web3ItemBlock


class Web3EthBaseBlock(Web3ItemBlock):
    """
    A class representing a base block for web3 eth operations.
    """

    def __init__(
        self,
        method: str,
        args: Dict[str, Any],
        BlockItem: Optional[type[Web3Item]] = Web3Item,
        key: Optional[str] = None,
        reference: Optional[str] = None,
    ) -> None:
        """
        Initializes a Web3EthBaseBlock instance.

        Args:
            method (str): The method to be called.
            args (Dict[str, Any]): The arguments to be passed to the method.
            BlockItem (Web3Item): The item to be used for the operation.
        """
        super().__init__(
            chain_id=self.__class__.getWeb3ChainId(),
            method=method,
            args=args,
            key=key,
            BlockItem=BlockItem,
            reference=reference,
        )

    @staticmethod
    def getWeb3ChainId() -> int:
        return 1

    @staticmethod
    def getWeb3Method() -> str:
        raise NotImplementedError("Subclasses must implement this method")
