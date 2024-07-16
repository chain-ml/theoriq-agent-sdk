from pydantic import BaseModel


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


class ExecuteRequest(BaseModel):
    items: list[DialogItem]


class ChallengeRequest(BaseModel):
    """Schema for a challenge request."""

    nonce: str


class ChallengeResponse(BaseModel):
    nonce: str
    signature: str
