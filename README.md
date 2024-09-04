# SDK for ***Theoriq*** agents

The purpose of this SDK is to streamline the integration of an Agent into the Theoriq Protocol for developers. A key feature of the SDK is its ability to abstract the security requirements necessary for an agent to participate in Theoriq. The only prerequisite for developers is to generate an ed25519 private key for the Agent.

This repository provides a framework for handling the execution of requests, responses, and associated errors in a highly modular and extensible way. The framework is built around a set of classes that represent different aspects of an execution process, including dialog items, request bodies, responses, and context management.

# Core Concepts

## Dialog and DialogItem

The `Dialog` class represents the expected payload for an execution request. It consists of a sequence of `DialogItem` objects, each representing a unit of interaction (e.g., a message or an event) within a conversation between a user and an agent.

***Attributes:***

`items`: A sequence of `DialogItem` objects, where each item represents interactions from the user and agents.

## ExecuteRequestBody

The `ExecuteRequestBody` class represents the body of an execution request. It contains the `Dialog` object and an optional `Configuration` object.

***Attributes:***

`dialog`: A `Dialog` object that encapsulates the request/response interactions.

***Methods:***

- `last_item`: Returns the last `DialogItem` based on the timestamp.
- `last_item_from`: Filters and returns the last `DialogItem` from a specific source type: either the `user` or an `agent`.

## ExecuteResponse

The `ExecuteResponse` class represents the result of an execution request. It encapsulates the response data, including the `DialogItem`, the cost of processing, and the status code.

***Attributes:***

- `body`: The `DialogItem` representing the body of the response.
- `theoriq_cost`: The cost associated with processing the request, represented by a `TheoriqCost` object.
- `status_code`: The status code of the response (e.g., 200 for success).

## ExecuteContext

The `ExecuteContext` class is central to managing the execution process. It holds the context for the execution, including the agent, protocol client, and request biscuit.

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

`ExecuteRuntimeError` is a custom exception class that represents runtime errors during the execution of a request.

***Attributes:***

- `err`: The error code or message.
- `message`: An optional message providing additional context for the error.

### Initialization

The constructor allows for both an error code and an additional message, which are combined into a single error message if both are provided.


# Installation

```shell
pip install -r requirements.txt
```


# Example

## HelloWorld Agent

Build a very simple HelloWorld Agent

## Creating the Private Key

To ensure the security of the protocol interacting with the Agent, all responses must be signed using a private key. This private key is critical for validating and authenticating the responses.

### Steps to Generate the Private Key

1. **Run the Script**:
   - Navigate to the `script` folder in your project directory.
   - Execute the `generate_private_key` script to generate the private key.

2. **Expected Output**:
   - Upon successful execution, the output should resemble the following:
     ```text
     AGENT_PRIVATE_KEY = 0x5f83410.....................05eb..........................2da3fe0
     Corresponding public key: `0x8b75889be1559d86e47f033624881fcd055deacad13807a202f23685c77f172c`
     ```
     
Keep the public key for the Agent registration within the Infinity Hub.

### Important Notes

- **Confidentiality**: This private key is extremely sensitive and should be stored securely. Under no circumstances should this key be shared with anyone, including any members of Theoriq.
- **Security**: Ensure that the key is kept in a secure environment to prevent unauthorized access.
- **Uniqueness**: A new private key should be generated for each agent.

By following these steps and precautions, you will maintain the integrity and security of the protocol interactions with the Agent.

## Core of the Agent

Writing the core function of an `HelloWorld` Agent

```python
def execute(context: ExecuteContext, req: ExecuteRequestBody) -> ExecuteResponse:
    logger.info(f"Received request: {context.request_id}")
    
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
```

## Exposing the Agent's Endpoint

Let's expose the Agent endpoint with a Flask server.
You can define a `requirements.txt` like:
```text
python-dotenv==1.0.*
flask==3.0.*

git+ssh://git@github.com/chain-ml/theoriq-agent-sdk.git#egg=theoriq[flask]
```

Code of your `main.py`. 

```python
if __name__ == "__main__":
    app = Flask(__name__)

    # Load agent configuration from env
    dotenv.load_dotenv()
    agent_config = AgentConfig.from_env()

    # Create and register theoriq blueprint
    blueprint = theoriq_blueprint(agent_config, execute)
    app.register_blueprint(blueprint)
    app.run(host="0.0.0.0", port=8000)
```

## Deploy and Start your Agent

For the deployment process ensure to define those 2 environment variables:
- `AGENT_PRIVATE_KEY` with the value created during the first step.
- `THEORIQ_URI` with the following value `https://theoriq-backend.chainml.net`


## Register the Agent in the Infinity Hub

Go and register your agent [here](https://infinity.theoriq.ai/hub/agent-register).

## Result

![Result in Infinity Studio](./doc/HellowWorld%20Session.png)