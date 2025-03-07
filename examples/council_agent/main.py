import logging
import os
from typing import List

import dotenv
from council.llm import AnthropicLLM, LLMConfigObject, LLMFunction, LLMMessage
from flask import Flask

from theoriq import AgentDeploymentConfiguration, ExecuteContext, ExecuteResponse
from theoriq.api.v1alpha2.schemas import ExecuteRequestBody
from theoriq.biscuit import TheoriqCost
from theoriq.dialog import TextItemBlock
from theoriq.extra.flask.v1alpha2.flask import theoriq_blueprint
from theoriq.types import Currency

logger = logging.getLogger(__name__)
dotenv.load_dotenv()


PROMPT_GENERATION = """You are a humorist specializing in dad jokes about a given topic. 
Generate only one short, clever, and family-friendly dad jokes that are pun-filled and guaranteed to make people smile. 
Keep them light-hearted and suitable for all ages.
Respond with only the Joke, no other text or explanation"""


def execute(context: ExecuteContext, req: ExecuteRequestBody) -> ExecuteResponse:
    logger.info(f"Received request: {context.request_id}")

    # Get the last `TextItemBlock` from the Dialog
    messages: List[LLMMessage] = []
    for item in req.dialog.items:
        last_block = item.blocks[0]
        if isinstance(last_block, TextItemBlock):
            if item.source_type.is_user:
                messages.append(LLMMessage.user_message(last_block.data.text))
            elif item.source_type.is_agent:
                messages.append(LLMMessage.assistant_message(last_block.data.text))

    # Core implementation of the Agent
    llm = AnthropicLLM.from_config(config)
    llm_gen_func: LLMFunction[str] = LLMFunction(llm, lambda x: x.value, PROMPT_GENERATION)
    llm_result = llm_gen_func.execute(messages=messages)

    # Wrapping the result into an `ExecuteResponse` with some helper functions on the Context
    blocks = [
        TextItemBlock(text=llm_result),
    ]
    return context.new_response(blocks=blocks, cost=TheoriqCost(amount=1, currency=Currency.USDC))


if __name__ == "__main__":
    app = Flask(__name__)

    # Load agent configuration from env
    agent_config = AgentDeploymentConfiguration.from_env()
    config = LLMConfigObject.from_yaml(os.path.join(os.path.dirname(__file__), "config.yaml"))

    # Create and register theoriq blueprint with v1alpha2 api version
    blueprint = theoriq_blueprint(agent_config, execute)
    app.register_blueprint(blueprint)
    app.run(host="0.0.0.0", port=8001)
