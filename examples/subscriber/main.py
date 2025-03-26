import asyncio
import logging
import os
import time

import dotenv
from flask import Flask

from theoriq import AgentDeploymentConfiguration, ExecuteContext, ExecuteResponse
from theoriq.api.v1alpha2 import SubscribeContext, Subscriber
from theoriq.api.v1alpha2.schemas import ExecuteRequestBody
from theoriq.api.v1alpha2.schemas.request import SubscribeRequestBody
from theoriq.biscuit import TheoriqCost
from theoriq.dialog import TextItemBlock, Web3EthSignBlock, Web3EthSignTypedDataBlock, Web3Item, Web3ItemBlock
from theoriq.extra.flask.v1alpha2.flask import theoriq_blueprint_with_subscriber
from theoriq.types import Currency

logger = logging.getLogger(__name__)


def execute(context: ExecuteContext, req: ExecuteRequestBody) -> ExecuteResponse:
    logger.info(
        f"Received request: {context.request_id} from {context.request_sender_type} {context.request_sender_address}"
    )
    if req.last_item is None:
        raise ValueError("Last item is required")

    # Get the last `TextItemBlock` from the Dialog
    last_block = req.last_item.blocks[0]
    text_value = last_block.data.text

    # Core implementation of the Agent
    agent_result = f"Hello {text_value} from a Theoriq Agent!"

    eth_typed_data_message_type = dict(
        domain={
            "name": "EIP712Domain",
            "version": "1",
            "chainId": 1,
            "salt": "0x0000000000000000000000000000000000000000000000000000000000000030",
            "verifyingContract": "0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC",
        },
        types={
            "EIP712Domain": [{"name": "name", "type": "string"}],
            "WelcomeMessage": [
                {"name": "from", "type": "string"},
                {"name": "to", "type": "address"},
                {"name": "message", "type": "string"},
            ],
        },
        primaryType="WelcomeMessage",
        message={"from": "Theoriq", "to": req.last_item.source or "User", "message": "Hello from Theoriq!"},
    )

    # Wrapping the result into an `ExecuteResponse` with some helper functions on the Context
    return context.new_response(
        blocks=[
            TextItemBlock(text=agent_result),
            Web3ItemBlock(item=Web3Item(chain_id=1, method="personal_sign", args={"message": "Hello Web3 World"})),
            Web3EthSignBlock(message="Hello Web3 World", method="personal_sign"),
            Web3EthSignBlock(message="Hello Web3 World", method="eth_sign"),
            Web3EthSignTypedDataBlock(data=eth_typed_data_message_type),
        ],
        cost=TheoriqCost(amount=1, currency=Currency.USDC),
    )


def subscribe(context: SubscribeContext, req: SubscribeRequestBody) -> None:
    logger.info(f"Received a new notification: {context.agent_address}")
    logger.info(f"Received notification: {req}")


def cleanup(context: SubscribeContext) -> None:
    print(f"Cleaning up: {context.agent_address}")


def stop_listener(subscriber: Subscriber, duration: int = 10) -> None:
    logger.info(f"will stop listener in {duration} seconds")
    time.sleep(duration)
    logger.info(f"Stopping listener: {subscriber.subscriber_id}")
    subscriber.stop_listener()
    logger.info(f"Listener stopped: {subscriber.subscriber_id}")


async def main():
    app = Flask(__name__)

    # Logging
    logging.basicConfig(level=logging.INFO)

    # Load agent configuration from env
    dotenv.load_dotenv()
    agent_config = AgentDeploymentConfiguration.from_env()

    # Create and register theoriq blueprint with v1alpha2 api version
    blueprint, subscription_manager, _ = theoriq_blueprint_with_subscriber(agent_config, execute)

    # Add a listener to the subscription manager
    publisher_agent_id = os.environ.get("PUBLISHER_AGENT_ID")
    if publisher_agent_id:
        subscriber = subscription_manager.new_listener(subscribe, publisher_agent_id, cleanup)
        print("new listener", subscriber)
        subscriber.start_listener()

    app.register_blueprint(blueprint)
    asyncio.create_task(asyncio.to_thread(stop_listener, subscriber, 5))
    await asyncio.gather(
        asyncio.to_thread(app.run, host="0.0.0.0", port=os.environ.get("FLASK_PORT", 8000)),
    )


if __name__ == "__main__":
    asyncio.run(main())
