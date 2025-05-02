import logging
import os

import dotenv

from theoriq.api.v1alpha2.protocol.biscuit_provider import BiscuitProviderFactory
from theoriq.api.v1alpha2.subscribe import Subscriber
from theoriq.biscuit import AgentAddress

logger = logging.getLogger(__name__)


def notification_handler(notification: str) -> None:
    logger.info(notification)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Load agent configuration from env
    dotenv.load_dotenv()
    publisher = AgentAddress.from_env("PUBLISHER_AGENT_ID")
    api_key = os.getenv("API_KEY")

    logger.info(f"Subscribing to agent {publisher}")

    subscriber = Subscriber(biscuit_provider=BiscuitProviderFactory.from_api_key(api_key=api_key))
    subscriber.new_job(agent_address=publisher, handler=notification_handler).start()
    logger.info(f"We have subscribed to the agent {publisher}.")
