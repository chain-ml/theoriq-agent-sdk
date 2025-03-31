import logging
import threading
import time
from typing import Callable, Optional

from typing_extensions import Self

from theoriq.api.v1alpha2.protocol.biscuit_provider import BiscuitProvider, BiscuitProviderFromAPIKey
from theoriq.api.v1alpha2.protocol.protocol_client import ProtocolClient

logger = logging.getLogger(__name__)


SubscribeJobFn = Callable[[str], None]


class Subscriber:
    def __init__(self, biscuit_provider: BiscuitProvider, client: Optional[ProtocolClient] = None) -> None:
        self._client = client or ProtocolClient.from_env()
        self._biscuit_provider = biscuit_provider

    def new_job(self, agent_id: str, subscribe_fn: SubscribeJobFn) -> threading.Thread:
        """
        Subscribe to an agent
        """

        def _subscribe() -> None:
            while True:
                biscuit = self._biscuit_provider.get_biscuit()
                for message in self._client.subscribe_to_agent_notifications(biscuit, agent_id):
                    subscribe_fn(message)
                time.sleep(1)  # wait for 1 second before reconnecting
                logger.warning("Connection to server lost. Reconnecting...")

        return threading.Thread(target=_subscribe)

    @classmethod
    def from_api_key(cls, api_key: str, client: Optional[ProtocolClient] = None) -> Self:
        """
        Create a Subscriber from an API key
        """
        protocol_client = client or ProtocolClient.from_env()
        biscuit_provider = BiscuitProviderFromAPIKey(api_key=api_key, client=protocol_client)
        return cls(biscuit_provider=biscuit_provider, client=protocol_client)
