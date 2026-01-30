from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable, Dict, Optional

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
                                notification=notification_message,
                                configuration=self._fetch_configuration(agent_address),
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

    def _fetch_configuration(self, agent_address: AgentAddress) -> Optional[Dict[str, Any]]:
        try:
            return self._client.get_configuration(
                request_biscuit=self._biscuit_provider.get_biscuit(),
                agent_address=agent_address,
                configuration_hash="hash",  # TODO
            )
        except RuntimeError:
            return None

    @classmethod
    def from_api_key(cls, api_key: str) -> Subscriber:
        return Subscriber(biscuit_provider=BiscuitProviderFactory.from_api_key(api_key=api_key))

    @classmethod
    def from_env(cls, env_prefix: str = "") -> Subscriber:
        return Subscriber(biscuit_provider=BiscuitProviderFactory.from_env(env_prefix=env_prefix))
