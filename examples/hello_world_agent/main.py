import logging
import os

import dotenv
from flask import Flask
from theoriq import AgentConfig, ExecuteContext, ExecuteResponse
from theoriq.biscuit import TheoriqCost
from theoriq.extra.flask import theoriq_blueprint
from theoriq.schemas import ExecuteRequestBody, TextItemBlock
from theoriq.types import Currency

logger = logging.getLogger(__name__)


def execute(context: ExecuteContext, req: ExecuteRequestBody) -> ExecuteResponse:
    logger.info(
        f"Received request: {context.request_id} from {context.request_sender_type} {context.request_sender_address}"
    )

    # Get the last `TextItemBlock` from the Dialog
    last_block = req.last_item.blocks[0]
    text_value = last_block.data.text

    # Core implementation of the Agent
    agent_result = f"Hello {text_value} from a Theoriq Agent!"

    # Wrapping the result into an `ExecuteResponse` with some helper functions on the Context
    return context.new_response(
        blocks=[
            TextItemBlock(text=agent_result),
        ],
        cost=TheoriqCost(amount=1, currency=Currency.USDC),
    )


if __name__ == "__main__":
    app = Flask(__name__)

    # Logging
    logging.basicConfig(level=logging.INFO)

    # Load agent configuration from env
    dotenv.load_dotenv()
    agent_config = AgentConfig.from_env()

    # Create and register theoriq blueprint
    blueprint = theoriq_blueprint(agent_config, execute)
    app.register_blueprint(blueprint)
    app.run(host="0.0.0.0", port=os.environ.get("FLASK_PORT", 8000))
