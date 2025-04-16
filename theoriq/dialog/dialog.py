from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Sequence, Type

from pydantic import BaseModel, field_serializer, field_validator

from ..types import SourceType
from .code import CodeItemBlock
from .custom import CustomItemBlock
from .data import DataItemBlock
from .image import ImageItemBlock
from .item_block import ItemBlock
from .metrics import MetricsItemBlock
from .router import RouteItem, RouterItemBlock
from .runtime_error import ErrorItemBlock
from .text import TextItemBlock
from .web3 import Web3Item, Web3ItemBlock

block_classes: Dict[str, Type[ItemBlock]] = {
    "code": CodeItemBlock,
    "custom": CustomItemBlock,
    "data": DataItemBlock,
    "error": ErrorItemBlock,
    "image": ImageItemBlock,
    "metrics": MetricsItemBlock,
    "router": RouterItemBlock,
    "text": TextItemBlock,
    "web3": Web3ItemBlock,
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
        self.timestamp: datetime = self._datetime_from_str(timestamp)
        self.source = source
        self.source_type = SourceType.from_value(source_type)
        self.blocks = blocks

    @classmethod
    def _datetime_from_str(cls, value: str) -> datetime:
        try:
            if re.search(r"\.\d+Z$", value):
                result = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
            else:
                result = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            result = datetime.fromisoformat(value)
        return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result

    @classmethod
    def from_dict(cls, values: Any | None) -> DialogItem:
        if values is None:
            raise ValueError("Cannot create a DialogItem from None")

        if not isinstance(values, dict):
            raise ValueError(f"Expect a dictionary, got {type(values)}")

        item_blocks: List[ItemBlock[Any]] = []
        blocs = values.get("blocks", [])
        for item in blocs:
            block_type: str = item["type"]
            bloc_class = block_classes.get(ItemBlock.root_type(block_type))
            if bloc_class is not None:
                block_data = item["data"]
                block_key = item.get("key", None)
                block_ref = item.get("ref", None)
                item_blocks.append(bloc_class.from_dict(block_data, block_type, block_key, block_ref))
            else:
                raise ValueError(f"invalid item type {block_type}")

        return cls(
            timestamp=values["timestamp"],
            source_type=values["sourceType"],
            source=values["source"],
            blocks=item_blocks,
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
            source_type=SourceType.from_address(source).value,
            source=source,
            blocks=blocks,
        )

    @classmethod
    def new_text(cls, source: str, text: str) -> DialogItem:
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            source_type=SourceType.from_address(source).value,
            source=source,
            blocks=[TextItemBlock(text)],
        )

    @classmethod
    def new_route(cls, source: str, route: str, score) -> DialogItem:
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            source_type=SourceType.from_address(source).value,
            source=source,
            blocks=[RouterItemBlock([RouteItem(route, score)])],
        )

    @classmethod
    def new_web3(cls, source: str, chain_id: int, method: str, args: Dict[str, Any]) -> DialogItem:
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            source_type=SourceType.from_address(source).value,
            source=source,
            blocks=[Web3ItemBlock(item=Web3Item(chain_id=chain_id, method=method, args=args))],
        )


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
                except ValueError:
                    raise
                except Exception as e:
                    raise ValueError from e

        return items

    @field_serializer("items")
    def serialize_items(self, value: Sequence[DialogItem]):
        return [item.to_dict() for item in value]

    class Config:
        arbitrary_types_allowed = True
