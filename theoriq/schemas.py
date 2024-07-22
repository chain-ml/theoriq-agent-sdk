from pydantic import BaseModel

from theoriq.types import RequestBiscuit


class DialogItemBlock(BaseModel):
    """Schema for dialog item block."""

    type: str
    data: str


class DialogItem(BaseModel):
    """Schema for dialog item."""

    timestamp: str
    source: str
    sourceType: str
    items: list[DialogItemBlock]


class ExecuteRequestBody(BaseModel):
    items: list[DialogItem]


class ExecuteRequest:
    """Request used when calling the `execute` endpoint"""

    def __init__(self, body: ExecuteRequestBody, biscuit: RequestBiscuit):
        self.body = body
        self.biscuit = biscuit


class ChallengeRequestBody(BaseModel):
    """Schema for a challenge request."""

    nonce: str


class ChallengeResponseBody(BaseModel):
    """Schema for a challenge request."""

    nonce: str
    signature: str
