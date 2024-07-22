"""
schemas.py

This module contains the schemas used by the theoriq endpoint.
"""

from pydantic import BaseModel


class DialogItemBlock(BaseModel):
    """
    Represents a specific dialogue item block within a DialogItem.

    A DialogItemBlock is an individual component in a ConversationItem's list of items.
    Each block contains data of a specific type which could be one of several formats such as text, markdown or code.

    Attributes:
        type (str): Specifies the format of the text in the block.
        data (str): Contains the actual response in the specified format.
    """

    type: str
    data: str


class DialogItem(BaseModel):
    """
    A DialogItem object represents a message from a source during a dialog.

    A single DialogItem contains multiple instances of DialogItemBlock. This allows an agent to send
    multi-format responses for a single request. An agent, for example, can send Python and SQL code blocks
    along with a markdown block.

    Attributes:
        timestamp (str): The creation time of the dialog item.
        source (str): The creator of the dialog item. In the agent context, this is the agent's ID in the Theoriq protocol.
        sourceType (str): The type of the source that creates the dialog item. Can be either 'user' or 'agent'.
        items (list[DialogItemBlock]): A list of DialogItemBlock objects consisting of responses from the agent.
    """

    timestamp: str
    source: str
    sourceType: str
    items: list[DialogItemBlock]


class ExecuteRequestBody(BaseModel):
    """
    Represents the expected payload for an execute request.

    Attributes:
        items (list[DialogItemBlock]): A list of DialogItemBlock objects consisting of request/response from the user and agent.
    """

    items: list[DialogItem]


class ChallengeRequestBody(BaseModel):
    """
    Represents the expected payload for a challenge request.

    Attributes:
        nonce (str): Hex encoded string containing the challenge nonce that needs to be signed by the agent.
    """

    nonce: str


class ChallengeResponseBody(BaseModel):
    """
    Represents the response payload for a challenge request.

    Attributes:
        nonce (str): Hex encoded string containing the nonce that has been signed by the agent.
        signature (str): Hex encoded string containing the challenge signature.
    """

    nonce: str
    signature: str
