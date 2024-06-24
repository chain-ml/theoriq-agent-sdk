"""Theoriq types"""

import string


class AgentAddress:
    """
    Address of an agent registered on the `theoriq` protocol
    Agent's address must be a 32 bytes hex encoded string
    """

    def __init__(self, address: str):
        self._verify_address(address)
        self.address = address

    @staticmethod
    def _verify_address(address: str) -> None:
        """
        Verify the address
        :raise TypeError: if the address is not 32 bytes long or does not only contain hex digits
        """
        AgentAddress._verify_address_length(address)
        AgentAddress._verify_address_content(address)

    @staticmethod
    def _verify_address_length(address: str) -> None:
        if len(address) != 32:
            raise TypeError(f"address must be 32 bytes long: {address}")

    @staticmethod
    def _verify_address_content(address: str) -> None:
        if not all(c in string.hexdigits for c in address):
            raise TypeError(f"address must only contain hex digits: {address}")

    def __str__(self) -> str:
        return self.address
