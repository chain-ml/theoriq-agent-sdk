from typing import Annotated

from pydantic import BaseModel, Field


class BiscuitResponseData(BaseModel):
    expires_at: Annotated[int, Field(alias="expiresAt")]
    subject: str


class BiscuitResponse(BaseModel):
    """
    Represents the response payload for a biscuit request.

    Attributes:
        biscuit (str): Base64 encoded string containing the biscuit.
    """

    biscuit: str
    data: BiscuitResponseData
