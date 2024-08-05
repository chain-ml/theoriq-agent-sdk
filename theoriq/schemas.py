"""
schemas.py

This module contains the schemas used by the Theoriq endpoint.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, Sequence, TypeVar, Union

from pydantic import BaseModel, field_serializer, field_validator


class BaseData(ABC):
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass


T_Data = TypeVar("T_Data", bound=Union[BaseData, Sequence[BaseData]])


class ItemBlock(Generic[T_Data]):
    """ """

    def __init__(
        self, *, bloc_type: str, data: T_Data, key: Optional[str] = None, reference: Optional[str] = None
    ) -> None:
        self.bloc_type = bloc_type
        self.data = data
        self.key = key
        self.reference = reference

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"type": self.bloc_type}
        if isinstance(self.data, BaseData):
            result["data"] = self.data.to_dict()
        elif isinstance(self.data, Sequence):
            result["data"] = {"items": [d.to_dict() for d in self.data]}

        if self.key is not None:
            result["key"] = self.key
        if self.reference is not None:
            result["ref"] = self.reference
        return result


class RouteItem(BaseData):
    """ """

    def __init__(self, name: str, score: float):
        self.name = name
        self.score = score

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "score": self.score}

    @classmethod
    def from_dict(cls, values: Dict[str, Any]) -> RouteItem:
        return cls(name=values["name"], score=values["score"])


class RouteItemBlock(ItemBlock[Sequence[RouteItem]]):
    """ """

    def __init__(self, routes: Sequence[RouteItem]):
        super().__init__(bloc_type="route", data=routes)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RouteItemBlock:
        items = data.get("items", [])
        return cls(routes=[RouteItem.from_dict(route) for route in items])


class TextItem(BaseData):
    """ """

    def __init__(self, text: str):
        self.text = text

    def to_dict(self) -> Dict[str, Any]:
        return {"text": self.text}


class TextItemBlock(ItemBlock[TextItem]):
    """ """

    def __init__(self, text: str, sub_type: Optional[str] = None):
        sub_type = f":{sub_type}" if sub_type is not None else ""
        super().__init__(bloc_type=f"text{sub_type}", data=TextItem(text=text))

    @classmethod
    def from_dict(cls, data: Any):
        return cls(text=data["text"])


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
        items (list[ItemBlock]): A list of ItemBlock objects consisting of responses from the agent.
    """

    def __init__(self, timestamp: str, source_type: str, source: str, blocks: List[ItemBlock[Any]]):
        self.timestamp = timestamp
        self.source = source
        self.source_type = source_type
        self.blocks = blocks

    @classmethod
    def from_dict(cls, values: Any | None) -> DialogItem:
        if values is None:
            raise ValueError("Cannot create a DialogItem from None")

        blocks: List[ItemBlock[Any]] = []
        for item in values["blocks"]:
            block_type: str = item["type"]
            if block_type.startswith("text"):
                blocks.append(TextItemBlock.from_dict(item["data"]))
            if block_type == "route":
                blocks.append(RouteItemBlock.from_dict(item["data"]))

        return cls(
            timestamp=values["timestamp"],
            source_type=values["sourceType"],
            source=values["source"],
            blocks=blocks,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "sourceType": self.source_type,
            "source": self.source,
            "blocks": [block.to_dict() for block in self.blocks],
        }

    @classmethod
    def new(cls, source: str, items: List[ItemBlock[Any]]) -> DialogItem:
        return cls(timestamp=datetime.now(timezone.utc).isoformat(), source_type="Agent", source=source, blocks=items)

    @classmethod
    def new_text(cls, source: str, text: str) -> DialogItem:
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            source_type="Agent",
            source=source,
            blocks=[TextItemBlock(text)],
        )

    @classmethod
    def new_route(cls, source: str, route: str, score) -> DialogItem:
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            source_type="Agent",
            source=source,
            blocks=[RouteItemBlock([RouteItem(route, score)])],
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
