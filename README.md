# SDK for ***Theoriq*** agents

The purpose of this SDK is to streamline the integration of an Agent into the Theoriq Protocol for developers. A key feature of the SDK is its ability to abstract the security requirements necessary for an agent to participate in Theoriq. The only prerequisite for developers is to generate an ed25519 private key for the Agent.

This repository provides a framework for handling the execution of requests, responses, and associated errors in a highly modular and extensible way. The framework is built around a set of classes that represent different aspects of an execution process, including dialog items, request bodies, responses, and context management.

# Core Concepts

## Dialog and DialogItem

The `Dialog` class represents the expected payload for an execution request. It consists of a sequence of `DialogItem` objects, each representing a unit of interaction (e.g., a message or an event) within a conversation between a user and an agent.

***Attributes:***

`items`: A sequence of `DialogItem` objects, where each item represents a interactions from the user and agents.

## ExecuteRequestBody

The `ExecuteRequestBody`  class represents the body of an execution request. It contains the Dialog object and an optional Configuration object.

***Attributes:***

`dialog`: A `Dialog` object that encapsulates the request/response interactions.

***Methods:***

- `last_item`: Returns the last `DialogItem` based on the timestamp.
- `last_item_from`: Filters and returns the last DialogItem from a specific source type either the `user` or an `agent`.

## ExecuteResponse

The ExecuteResponse class represents the result of an execution request. It encapsulates the response data, including the DialogItem, the cost of processing, and the status code.

***Attributes:***

- `body`: The DialogItem representing the body of the response.
- `theoriq_cost`: The cost associated with processing the request, represented by a TheoriqCost object.
- `status_code`: The status code of the response (e.g., 200 for success).

## ExecuteContext

The ExecuteContext class is central to managing the execution process. It holds the context for the execution, including the agent, protocol client, and request biscuit.

***Methods:***

- `send_event`: Sends an event message using the protocol client.
- `new_error_response_biscuit`: Creates a new response biscuit in case of an error.
- `new_free_response`: Creates a new response with zero cost.
- `new_response`: Creates a new response with specified blocks and cost.
- `runtime_error_response`: Generates a response for a runtime error.
- `send_request`: Sends a request to another address, handling the response and cost.

***Properties:***
- `agent_address`: Returns the agent's address.
- `request_id`: Returns the request ID from the request biscuit.
- `budget`: Returns the budget associated with the request.

## ExecuteRuntimeError

ExecuteRuntimeError is a custom exception class that represents runtime errors during the execution of a request.

***Attributes:***

- `err`: The error code or message.
- `message`: An optional message providing additional context for the error.

### Initialization:

The constructor allows for both an error code and an additional message, which are combined into a single error message if both are provided.


# Example

Writing the core function of an HeloWorld Agent

```python
def execute(context: ExecuteContext, req: ExecuteRequestBody) -> ExecuteResponse:
    logger.info(f"Received request: {context.request_id}")
    
    # Get the last `TextItemBlock` from the Dialog
    last_block = req.last_item.blocks[0]
    text_value = last_block.data.text

    tokens = text_value.split(" ", 1)
    if tokens[0].startswith("error"):
        raise ExecuteRuntimeError(f"This is an error: {tokens[-1]}", message="Occurs because the prompt starts with error")

    # Core implementation of the Agent
    agent_result = f"Hello {text_value} from a Theoriq simple Agent!"
    
    # Wrapping the result into an `ExecuteResponse` with some helper functions on the Context
    return context.new_response(
        blocks=[
            TextItemBlock(text=agent_result),
        ],
        cost=TheoriqCost(amount=0.01, currency=Currency.USDC),
    )

```