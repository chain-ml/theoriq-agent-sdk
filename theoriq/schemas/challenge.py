from pydantic import BaseModel


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
