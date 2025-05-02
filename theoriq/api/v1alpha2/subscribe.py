import logging
import threading
import time
from typing import Callable

import httpx

from theoriq.biscuit import AgentAddress

from ..common import AuthRepresentative

logger = logging.getLogger(__name__)


# Type alias for a function that handles subscription messages
# The function takes a message string as input and returns nothing
SubscribeHandlerFn = Callable[[str], None]


class Subscriber(AuthRepresentative):
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
            while True:
                try:
                    biscuit = self._biscuit_provider.get_biscuit()
                    for message in self._client.subscribe_to_agent_notifications(biscuit, agent_address.address):
                        handler(message)
                    logger.warning("Connection to server lost. Reconnecting...")
                except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as e:
                    logger.warning(f"Something went wrong: {e}. Retrying...")
                time.sleep(1)  # wait for 1 second before reconnecting

        return threading.Thread(target=_subscribe_job, daemon=background)
