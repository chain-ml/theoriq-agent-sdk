from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Type

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

BLOCK_CLASSES_MAP: Mapping[str, Type[ItemBlock]] = {
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

    A single DialogItem contains multiple instances of ItemBlock.
    This allows an agent to send multi-format responses for a single request.
    For example, it can send Python and SQL code blocks along with a Markdown text block.

    Attributes:
        timestamp (str): The creation time of the dialog item.
        source (str): The creator of the dialog item. Either user address or Theoriq agent ID.
        source_type (str): The type of the source that creates the dialog item. Can be either 'user' or 'agent'.
        blocks (Sequence[ItemBlock]): A sequence of ItemBlock objects consisting of responses from the agent.
    """

    def __init__(self, timestamp: str, source_type: str, source: str, blocks: Sequence[ItemBlock[Any]]) -> None:
        self.timestamp: datetime = self._datetime_from_str(timestamp)
        self.source = source
        self.source_type = SourceType.from_value(source_type)
        self.blocks = list(blocks)

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
        blocks = values.get("blocks", [])
        for item in blocks:
            block_type: str = item["type"]
            block_class = BLOCK_CLASSES_MAP.get(ItemBlock.root_type(block_type))
            if block_class is None:
                raise ValueError(f"Invalid item type {block_type}")

            block_data = item["data"]
            block_key = item.get("key", None)
            block_ref = item.get("ref", None)
            item_blocks.append(block_class.from_dict(block_data, block_type, block_key, block_ref))

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

    def format_source(self, with_address: bool = True) -> str:
        """Format the string describing the creator of the dialog item."""
        source_type = self.source_type.value.capitalize()
        return source_type if not with_address else f"{source_type} ({self.source})"

    def format(self, block_types_to_format: Optional[Sequence[Type[ItemBlock]]] = None) -> List[str]:
        """Format all blocks in the current dialog item."""

        results: List[str] = []
        for block in self.blocks:
            if block_types_to_format is None:
                results.append(block.data.to_str())
                continue

            for block_type in block_types_to_format:
                if block_type.is_valid(block.block_type()):
                    results.append(block.data.to_str())

        return results

    @classmethod
    def new(cls, source: str, blocks: Sequence[ItemBlock[Any]]) -> DialogItem:
        """Create a new instance with current datetime, deriving `source_type` from `source`."""
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            source_type=SourceType.from_address(source).value,
            source=source,
            blocks=blocks,
        )

    @classmethod
    def new_text(cls, source: str, text: str) -> DialogItem:
        return DialogItem.new(source=source, blocks=[TextItemBlock(text)])

    @classmethod
    def new_route(cls, source: str, route: str, score: float) -> DialogItem:
        return DialogItem.new(source=source, blocks=[RouterItemBlock([RouteItem(route, score)])])

    @classmethod
    def new_web3(cls, source: str, chain_id: int, method: str, args: Dict[str, Any]) -> DialogItem:
        return DialogItem.new(
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
    def validate_items(cls, value: Any) -> List[DialogItem]:
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
    def serialize_items(self, value: Sequence[DialogItem]) -> List[Dict[str, Any]]:
        return [item.to_dict() for item in value]

    class Config:
        arbitrary_types_allowed = True
