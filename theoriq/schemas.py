"""
schemas.py

This module contains the schemas used by the Theoriq endpoint.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Sequence, TypeVar, Generic

from pydantic import BaseModel, field_validator, field_serializer

T_Data = TypeVar("T_Data")


class ItemBlock(Generic[T_Data]):
    """ """

    def __init__(self, *, bloc_type: str, data: T_Data):
        self.bloc_type = bloc_type
        self.data = data

    def to_dict(self):
        # Convert the object to a dictionary
        return {"type": self.bloc_type, "data": self.data}


class RouteItem:
    """ """

    def __init__(self, name: str, score: float):
        self.name = name
        self.score = score

    @classmethod
    def from_dict(cls, values: Dict[str, Any]) -> RouteItem:
        return cls(name=values["name"], score=values["score"])


class RouteItemBlock(ItemBlock[Sequence[RouteItem]]):
    """ """

    def __init__(self, routes: Sequence[RouteItem]):
        super().__init__(bloc_type="route", data=routes)

    @classmethod
    def from_dict(cls, data: Any):
        return cls(routes=[RouteItem.from_dict(route) for route in data])


class DialogItemBlock(ItemBlock[str]):
    """ """

    def __init__(self, text: str):
        super().__init__(bloc_type="text", data=text)


class DialogItem:
    """
    A DialogItem object represents a message from a source during a dialog.

    A single DialogItem contains multiple instances of DialogItemBlock. This allows an agent to send
    multi-format responses for a single request. An agent, for example, can send Python and SQL code blocks
    along with a markdown block.

    Attributes:
        timestamp (str): The creation time of the dialog item.
        source (str): The creator of the dialog item. In the agent context, this is the agent's ID in the Theoriq protocol.
        source_type (str): The type of the source that creates the dialog item. Can be either 'user' or 'agent'.
        items (list[DialogItemBlock]): A list of DialogItemBlock objects consisting of responses from the agent.
    """

    def __init__(self, timestamp: str, source_type: str, source: str, items: List[ItemBlock[Any]]):
        self.timestamp = timestamp
        self.source = source
        self.source_type = source_type
        self.items = items

    @classmethod
    def from_dict(cls, values: Any | None) -> DialogItem:
        if values is None:
            raise ValueError("Cannot create a DialogItem from None")

        items: List[ItemBlock[Any]] = []
        for item in values["items"]:
            block_type: str = item["type"]
            if block_type.startswith("text"):
                items.append(DialogItemBlock(text=item["data"]))
            if block_type == "route":
                items.append(RouteItemBlock.from_dict(item["data"]))

        return cls(
            timestamp=values["timestamp"],
            source_type=values["sourceType"],
            source=values["source"],
            items=items,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "sourceType": self.source_type,
            "source": self.source,
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def new(cls, source: str, items: List[ItemBlock[Any]]) -> DialogItem:
        return cls(timestamp=datetime.now(timezone.utc).isoformat(), source_type="Agent", source=source, items=items)

    @classmethod
    def new_text(cls, source: str, text: str) -> DialogItem:
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            source_type="Agent",
            source=source,
            items=[DialogItemBlock(text)],
        )

    @classmethod
    def new_route(cls, source: str, route: str, score) -> DialogItem:
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            source_type="Agent",
            source=source,
            items=[RouteItemBlock([RouteItem(route, score)])],
        )


class ExecuteRequestBody(BaseModel):
    """
    Represents the expected payload for an execute request.

    Attributes:
        items (list[DialogItem]): A list of DialogItem objects consisting of request/response from the user and agent.
    """

    items: Sequence[DialogItem]

    @field_validator("items", mode="before")
    def validate_items(cls, value):
        if not isinstance(value, Sequence):
            raise ValueError("items must be a sequence")

        items = []
        for item in value:
            if isinstance(item, DialogItem):
                items.append(item)
            else:
                try:
                    dialog_item = DialogItem.from_dict(item)
                    items.append(dialog_item)
                except Exception as e:
                    raise ValueError from e

        return items

    @field_serializer("items")
    def serialize_items(cls, value):
        return [item.to_dict() for item in value]

    class Config:
        arbitrary_types_allowed = True


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
