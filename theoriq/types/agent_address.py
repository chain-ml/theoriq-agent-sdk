"""Theoriq types"""


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
        try:
            if len(bytes.fromhex(address)) != 32:
                raise TypeError(f"address must be 32 bytes long: {address}")
        except ValueError:
            raise TypeError(f"address must only contain hex digits: {address}")

    def __str__(self) -> str:
        return self.address
