from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Type

from pydantic import BaseModel, field_serializer, field_validator

from ..types import SourceType
from .code import CodeItemBlock
from .custom import CustomItemBlock
from .data import DataItemBlock
from .image import ImageItemBlock
from .metrics import MetricsItemBlock
from .router import RouteItem, RouterItemBlock
from .runtime_error import ErrorItemBlock
from .schemas import ItemBlock
from .text import TextItemBlock

block_classes: Dict[str, Type[ItemBlock]] = {
    "code": CodeItemBlock,
    "custom": CustomItemBlock,
    "data": DataItemBlock,
    "error": ErrorItemBlock,
    "image": ImageItemBlock,
    "metrics": MetricsItemBlock,
    "router": RouterItemBlock,
    "text": TextItemBlock,
}


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
        blocks (list[ItemBlock]): A list of ItemBlock objects consisting of responses from the agent.
    """

    def __init__(self, timestamp: str, source_type: str, source: str, blocks: Sequence[ItemBlock[Any]]) -> None:
        self.timestamp: datetime = datetime.fromisoformat(timestamp)
        self.source = source
        self.source_type = SourceType.from_value(source_type)
        self.blocks = blocks

    @classmethod
    def from_dict(cls, values: Any | None) -> DialogItem:
        if values is None:
            raise ValueError("Cannot create a DialogItem from None")

        blocks: List[ItemBlock[Any]] = []
        for item in values["blocks"]:
            block_type: str = item["type"]
            bloc_class = block_classes.get(ItemBlock.root_type(block_type))
            if bloc_class is not None:
                block_data = item["data"]
                blocks.append(bloc_class.from_dict(block_data, block_type))
            else:
                raise ValueError(f"invalid item type {block_type}")

        return cls(
            timestamp=values["timestamp"],
            source_type=values["sourceType"],
            source=values["source"],
            blocks=blocks,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "sourceType": self.source_type.value,
            "source": self.source,
            "blocks": [block.to_dict() for block in self.blocks],
        }

    def find_blocks_of_type(self, block_type: str) -> Iterable[ItemBlock[Any]]:
        for block in self.blocks:
            if block.block_type() == block_type:
                yield block
        return

    @classmethod
    def new(cls, source: str, blocks: Sequence[ItemBlock[Any]]) -> DialogItem:
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            source_type=SourceType.Agent.value,
            source=source,
            blocks=blocks,
        )

    @classmethod
    def new_text(cls, source: str, text: str) -> DialogItem:
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            source_type=SourceType.Agent.value,
            source=source,
            blocks=[TextItemBlock(text)],
        )

    @classmethod
    def new_route(cls, source: str, route: str, score) -> DialogItem:
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            source_type=SourceType.Agent.value,
            source=source,
            blocks=[RouterItemBlock([RouteItem(route, score)])],
        )


class Configuration(BaseModel):
    """
    Represents the expected payload for a configuration request.
    """


class ExecuteRequestBody(BaseModel):
    """
    A class representing the body of an execute request. Inherits from BaseModel.
    """

    configuration: Optional[Configuration] = None
    dialog: Dialog

    @property
    def last_item(self) -> Optional[DialogItem]:
        """
        Returns the last dialog item contained in the request based on the timestamp.

        Returns:
            Optional[DialogItem]: The dialog item with the most recent timestamp, or None if there are no items.
        """
        if len(self.dialog.items) == 0:
            return None
        # Finds and returns the dialog item with the latest timestamp.
        return max(self.dialog.items, key=lambda obj: obj.timestamp)

    def last_item_from(self, source_type: SourceType) -> Optional[DialogItem]:
        """
        Returns the last dialog item from a specific source type based on the timestamp.

        Args:
            source_type (SourceType): The source type to filter the dialog items.

        Returns:
            Optional[DialogItem]: The dialog item with the most recent timestamp from the specified source type,
                                  or None if no items match the source type.
        """
        # Filters items by source type and finds the one with the latest timestamp.
        return self.last_item_predicate(lambda item: item.source_type == source_type)

    def last_item_predicate(self, predicate: DialogItemPredicate) -> Optional[DialogItem]:
        """
        Returns the last dialog item that matches the given predicate based on the timestamp.

        Args:
            predicate (DialogItemPredicate): A function that takes a DialogItem and returns a boolean.

            Returns:
                Optional[DialogItem]: The dialog item that matches the predicate and has the latest timestamp,
                                       or None if no items match the predicate.
        """

        # Filters items matching the given predicate and finds the one with the latest timestamp.
        items = (item for item in self.dialog.items if predicate(item))
        return max(items, key=lambda obj: obj.timestamp) if items else None


DialogItemPredicate = Callable[[DialogItem], bool]


class Dialog(BaseModel):
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
    def serialize_items(self, value: Sequence[DialogItem]):
        return [item.to_dict() for item in value]

    class Config:
        arbitrary_types_allowed = True
