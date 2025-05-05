import logging
import time

import dotenv

from theoriq.api.v1alpha2.publish import Publisher, PublisherContext

logger = logging.getLogger(__name__)


def hello_job(context: PublisherContext) -> None:
    i = 0
    while True:
        time.sleep(2)
        try:
            context.publish(f"Hello World {i}!")
            i += 1
        except Exception:
            logger.exception("Failed to publish message")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Load agent configuration from env
    dotenv.load_dotenv()

    Publisher.from_env().new_job(job=hello_job).start()
