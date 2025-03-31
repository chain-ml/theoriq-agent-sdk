import logging
import threading
import time
from typing import Callable, Optional

from biscuit_auth import PrivateKey
from typing_extensions import Self

from theoriq.biscuit import AgentAddress

from .protocol.biscuit_provider import BiscuitProvider, BiscuitProviderFromAPIKey, BiscuitProviderFromPrivateKey
from .protocol.protocol_client import ProtocolClient

logger = logging.getLogger(__name__)


# Type alias for a function that handles subscription messages
# The function takes a message string as input and returns nothing
SubscribeHandlerFn = Callable[[str], None]


class Subscriber:
    def __init__(self, biscuit_provider: BiscuitProvider, client: Optional[ProtocolClient] = None) -> None:
        self._client = client or ProtocolClient.from_env()
        self._biscuit_provider = biscuit_provider

    def new_job(self, agent_address: AgentAddress, handler: SubscribeHandlerFn) -> threading.Thread:
        """
        Subscribe to an agent's notifications.

        Args:
            agent_address: The address of the agent to subscribe to
            handler: The handler function to call when a message is received

        Returns:
        """

        def _subscribe_job() -> None:
            while True:
                biscuit = self._biscuit_provider.get_biscuit()
                for message in self._client.subscribe_to_agent_notifications(biscuit, agent_address.address):
                    handler(message)
                time.sleep(1)  # wait for 1 second before reconnecting
                logger.warning("Connection to server lost. Reconnecting...")

        return threading.Thread(target=_subscribe_job)

    @classmethod
    def from_api_key(cls, api_key: str, client: Optional[ProtocolClient] = None) -> Self:
        """
        Create a Subscriber from an API key.

        Args:
            api_key: The API key used for authentication
            client: Optional protocol client, will create one from environment if not provided

        Returns:
            A new Subscriber instance configured with the API key credentials
        """
        protocol_client = client or ProtocolClient.from_env()
        biscuit_provider = BiscuitProviderFromAPIKey(api_key=api_key, client=protocol_client)
        return cls(biscuit_provider=biscuit_provider, client=protocol_client)

    @classmethod
    def from_agent(
        cls, private_key: PrivateKey, address: AgentAddress, client: Optional[ProtocolClient] = None
    ) -> Self:
        """
        Create a Subscriber from an agent's private key and address.

        Args:
            private_key: The agent's private key used for authentication
            address: The agent's address
            client: Optional protocol client, will create one from environment if not provided

        Returns:
            A new Subscriber instance configured with the agent's credentials
        """
        protocol_client = client or ProtocolClient.from_env()
        biscuit_provider = BiscuitProviderFromPrivateKey(
            private_key=private_key, address=address, client=protocol_client
        )
        return cls(biscuit_provider=biscuit_provider, client=protocol_client)
