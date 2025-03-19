from typing import Optional

from .. import Web3Item
from typing import Dict, Any

class Web3ResultItem(Web3Item):
    """
    A class representing the result of a Web3 item. Inherits from BaseData.
    """

    def __init__(self, *, chain_id: int, args: Dict[str, Any]) -> None:
        """
        Initializes a Web3Item instance.

        Args:
            chain_id (int): The chain_id that this web3 item is related to.
            method (str): The method that this web3Item will execute.
            args (List[str]): The arguments that this web3Item will execute with.
        """
        self.chain_id = chain_id
        self.method = self.__class__.getWeb3Method()
        self.args = args
    
    @staticmethod
    def getWeb3Method() -> str:
        return "result"

