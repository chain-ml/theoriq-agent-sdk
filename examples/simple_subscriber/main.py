import logging
import os

import dotenv

from theoriq.api.v1alpha2.subscribe import Subscriber

logger = logging.getLogger(__name__)


def notification_job(notification: str) -> None:
    logger.info(notification)


if __name__ == "__main__":

    # Logging
    logging.basicConfig(level=logging.INFO)

    # Load agent configuration from env
    dotenv.load_dotenv()
    publisher_agent_id = os.getenv("PUBLISHER_AGENT_ID")
    api_key = os.getenv("API_KEY")

    logger.info(f"Subscribing to agent {publisher_agent_id}")

    Subscriber.from_api_key(api_key=api_key).new_job(agent_id=publisher_agent_id, subscribe_fn=notification_job).start()
    logger.info(f"We have subscribed to the agent {publisher_agent_id}.")
