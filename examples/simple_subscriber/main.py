import logging
import os

import dotenv

from theoriq.extra.flask.v1alpha2 import subscribe_to_agent

logger = logging.getLogger(__name__)


def handle_notification(notification: str) -> None:
    logger.info(notification)


if __name__ == "__main__":

    # Logging
    logging.basicConfig(level=logging.INFO)

    # Load agent configuration from env
    dotenv.load_dotenv()
    publisher_agent_id = os.getenv("PUBLISHER_AGENT_ID")
    access_token = os.getenv("ACCESS_TOKEN")

    logger.info(f"Subscribing to agent {publisher_agent_id}")

    thread = subscribe_to_agent(publisher_agent_id, handle_notification, access_token)
    thread.start()
    logger.info(f"We have subscribed to the agent {publisher_agent_id}.")
