from pydantic import BaseModel


class BiscuitResponse(BaseModel):
    """
    Represents the response payload for a biscuit request.

    Attributes:
        biscuit (str): Base64 encoded string containing the biscuit.
    """

    biscuit: str
