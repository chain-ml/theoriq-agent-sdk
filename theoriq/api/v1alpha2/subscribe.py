from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable, Dict, Optional

from httpx import HTTPStatusError

from theoriq.biscuit import AgentAddress

from .protocol.biscuit_provider import BiscuitProvider, BiscuitProviderFactory
from .protocol.protocol_client import ProtocolClient
from .schemas.notification import NotificationContext

logger = logging.getLogger(__name__)


# Type alias for a function that handles subscription messages
# The function takes a NotificationContext as input and returns nothing
SubscribeHandlerFn = Callable[[NotificationContext], None]


class SubscriberStopException(Exception):
    pass


class Subscriber:
    """Enables subscribing to agent notifications."""

    def __init__(self, biscuit_provider: BiscuitProvider, client: Optional[ProtocolClient] = None) -> None:
        self._client = client or ProtocolClient.from_env()
        self._biscuit_provider = biscuit_provider
        self._configuration_hash: Optional[str] = None

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
                        for notification_message in self._client.subscribe_to_agent_notifications(
                            biscuit, agent_address.address
                        ):
                            notification = NotificationContext(
                                notification=notification_message, configuration=self._fetch_configuration()
                            )
                            handler(notification)
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

    def _fetch_configuration(self) -> Optional[Dict[str, Any]]:
        configuration_hash = self._get_configuration_hash()
        if configuration_hash is None:
            return None

        try:
            return self._client.get_configuration(
                request_biscuit=self._biscuit_provider.get_biscuit(),
                agent_address=AgentAddress(self._biscuit_provider.address),
                configuration_hash=configuration_hash,
            )
        except (RuntimeError, HTTPStatusError):  # ValueError, TypeError
            return None

    def _get_configuration_hash(self) -> Optional[str]:
        if self._configuration_hash is not None:
            return self._configuration_hash

        agent_metadata = self._client.get_agent(self._biscuit_provider.address, self._biscuit_provider.get_biscuit())
        if not agent_metadata.configuration.virtual:
            return None

        self._configuration_hash = agent_metadata.configuration.virtual.configuration_hash
        return self._configuration_hash

    @classmethod
    def from_api_key(cls, api_key: str) -> Subscriber:
        return Subscriber(biscuit_provider=BiscuitProviderFactory.from_api_key(api_key=api_key))

    @classmethod
    def from_env(cls, env_prefix: str = "") -> Subscriber:
        return Subscriber(biscuit_provider=BiscuitProviderFactory.from_env(env_prefix=env_prefix))


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
