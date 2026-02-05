from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable, Dict, Optional

from httpx import HTTPStatusError

from theoriq.biscuit import AgentAddress

from ...types import SourceType
from .protocol.biscuit_provider import BiscuitProvider, BiscuitProviderFactory
from .protocol.protocol_client import ProtocolClient
from .schemas.notification import NotificationContext

logger = logging.getLogger(__name__)


# Type alias for a function that handles subscription messages
# The function takes a message string as input and returns nothing
SubscribeHandlerFn = Callable[[str], None]

# Type alias for a function that handles subscription messages with context
# The function takes a NotificationContext as input and returns nothing
VirtualSubscribeHandlerFn = Callable[[NotificationContext], None]


class SubscriberStopException(Exception):
    pass


class Subscriber:
    """Enables subscribing to agent notifications."""

    def __init__(self, biscuit_provider: BiscuitProvider, client: Optional[ProtocolClient] = None) -> None:
        self._client = client or ProtocolClient.from_env()
        self._biscuit_provider = biscuit_provider

    def new_job(
        self, agent_address: AgentAddress, handler: SubscribeHandlerFn, background: bool = False
    ) -> threading.Thread:
        """
        Subscribe to an agent's notifications.

        Args:
            agent_address: The address of the agent to subscribe to
            handler: The handler function to call when a message is received
            background: Whether to run the job in the background

        Returns:
            A thread object that can be started to run the subscription job
        """

        def _subscribe_job() -> None:
            try:
                while True:
                    try:
                        biscuit = self._biscuit_provider.get_biscuit()
                        for message in self._client.subscribe_to_agent_notifications(biscuit, agent_address.address):
                            handler(message)
                        logger.warning("Connection to server lost. Reconnecting...")
                    except SubscriberStopException:
                        logger.info("Received stop exception")
                        return
                    except Exception as e:
                        logger.warning(f"Something went wrong: {e}. Retrying...")
                    time.sleep(1)  # wait for 1 second before reconnecting
            finally:
                logger.warning("End of subscription job")

        return threading.Thread(target=_subscribe_job, daemon=background)

    @classmethod
    def from_api_key(cls, api_key: str) -> Subscriber:
        return Subscriber(biscuit_provider=BiscuitProviderFactory.from_api_key(api_key=api_key))

    @classmethod
    def from_env(cls, env_prefix: str = "") -> Subscriber:
        return Subscriber(biscuit_provider=BiscuitProviderFactory.from_env(env_prefix=env_prefix))


class VirtualSubscriber:
    """Enables subscribing to agent notifications with virtual agent address and configuration support."""

    def __init__(
        self,
        biscuit_provider: BiscuitProvider,
        virtual_agent_address: AgentAddress,
        client: Optional[ProtocolClient] = None,
    ) -> None:
        self._client = client or ProtocolClient.from_env()
        self._biscuit_provider = biscuit_provider
        self._subscriber = Subscriber(biscuit_provider=self._biscuit_provider, client=self._client)
        self._virtual_agent_address = virtual_agent_address
        self._validate_virtual_agent_address()

        self._configuration_hash: Optional[str] = None

    def _validate_virtual_agent_address(self) -> None:
        """Ensure the provided address is a virtual agent address."""
        agent_metadata = self._client.get_agent(str(self._virtual_agent_address), self._biscuit_provider.get_biscuit())
        if not agent_metadata.configuration.is_virtual:
            raise ValueError(f"Agent {self._virtual_agent_address} is not a virtual agent")

    def new_job(
        self, agent_address: AgentAddress, handler: VirtualSubscribeHandlerFn, background: bool = False
    ) -> threading.Thread:
        """
        Subscribe to an agent's notifications.

        Args:
            agent_address: The address of the agent to subscribe to
            handler: The handler function to call when a message is received
            background: Whether to run the job in the background

        Returns:
            A thread object that can be started to run the subscription job
        """

        def wrapped_handler(message: str) -> None:
            notification = NotificationContext(notification=message, configuration=self._fetch_configuration())
            handler(notification)

        return self._subscriber.new_job(agent_address, wrapped_handler, background)

    def _fetch_configuration(self) -> Dict[str, Any]:
        return self._client.get_configuration(
            request_biscuit=self._biscuit_provider.get_biscuit(),
            agent_address=self._virtual_agent_address,
            configuration_hash=self._get_configuration_hash(),
        )

    def _get_configuration_hash(self) -> str:
        if self._configuration_hash is not None:
            return self._configuration_hash

        agent_metadata = self._client.get_agent(str(self._virtual_agent_address), self._biscuit_provider.get_biscuit())
        # ensure virtual is safe because of self._virtual_agent_address validated during construction
        self._configuration_hash = agent_metadata.configuration.ensure_virtual.configuration_hash
        return self._configuration_hash


class SubscriberBound:
    """A subscriber bound to a specific agent address for convenient subscription management."""

    def __init__(self, subscriber: Subscriber, agent_address: AgentAddress) -> None:
        self._subscriber = subscriber
        self._agent_address = agent_address

    @property
    def subscriber(self) -> Subscriber:
        return self._subscriber

    @property
    def agent_address(self) -> AgentAddress:
        return self._agent_address

    def new_job(self, handler: SubscribeHandlerFn, background: bool = False) -> threading.Thread:
        return self._subscriber.new_job(self.agent_address, handler, background)

    @classmethod
    def from_env(cls, agent_address_env_var: str, *, subscriber_env_prefix: str = "") -> SubscriberBound:
        return SubscriberBound(Subscriber.from_env(subscriber_env_prefix), AgentAddress.from_env(agent_address_env_var))
