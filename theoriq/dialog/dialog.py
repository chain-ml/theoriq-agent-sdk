from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Final, Iterable, List, Mapping, Optional, Sequence, Tuple, Type

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
from .web3 import Web3ProposedTxBlock, Web3SignedTxBlock
from .actions import ActionItem, ActionsItemBlock

BLOCK_CLASSES: Final[List[Type[ItemBlock]]] = [
    CodeItemBlock,
    CustomItemBlock,
    DataItemBlock,
    ErrorItemBlock,
    ImageItemBlock,
    MetricsItemBlock,
    RouterItemBlock,
    TextItemBlock,
    Web3ProposedTxBlock,
    Web3SignedTxBlock,
    ActionsItemBlock,
]
BLOCK_CLASSES_MAP: Mapping[str, Type[ItemBlock]] = {block_cls.block_type(): block_cls for block_cls in BLOCK_CLASSES}


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
            block_class = BLOCK_CLASSES_MAP.get(ItemBlock.root_type(block_type))  # try root type first
            if block_class is None:
                block_class = BLOCK_CLASSES_MAP.get(block_type)  # then try full type
                if block_class is None:
                    raise ValueError(
                        f"Invalid item type {block_type}, expected one of {', '.join(BLOCK_CLASSES_MAP.keys())}"
                    )

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

    def extract_last_text(self) -> str:
        """
        Returns the text from the last text block from the dialog item.

        Returns:
            str: Text from the last text.

        Raises:
            RuntimeError: If no text blocks are found in the dialog item.
        """

        text_blocks = list(self.find_blocks_of_type("text"))
        if len(text_blocks) == 0:
            raise RuntimeError("No text blocks found in the dialog item")

        return text_blocks[-1].data.text

    def format_source(self, with_address: bool = True) -> str:
        """Format the string describing the creator of the dialog item."""
        source_type = self.source_type.value.capitalize()
        return source_type if not with_address else f"{source_type} ({self.source})"

    def format_blocks(self, block_types_to_format: Optional[Sequence[Type[ItemBlock]]] = None) -> List[str]:
        """
        Format each block with `to_str()` whose type is in `block_types_to_format`.
        If `block_types_to_format` is None, format every block.
        """

        if block_types_to_format is None:
            return [block.data.to_str() for block in self.blocks]

        return [
            block.data.to_str()
            for block in self.blocks
            if any(block_type.is_valid(block.block_type()) for block_type in block_types_to_format)
        ]

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
    def new_actions(cls, source: str, actions: Sequence[ActionItem], key: Optional[str] = None) -> DialogItem:
        """Create a DialogItem that proposes a list of actions to the user."""
        block = ActionsItemBlock(actions, key=key)
        return DialogItem.new(source=source, blocks=[block])

    def __str__(self) -> str:
        source_str = f"{self.source[:6]}...{self.source[-4:]}"
        return f"DialogItem(timestamp={self.timestamp}, source_type={self.source_type}, source={source_str}, n_blocks={len(self.blocks)})"


DialogItemPredicate = Callable[[DialogItem], bool]
DialogItemTransformer = Callable[[DialogItem], Any]


def format_source_and_blocks(
    item: DialogItem, with_address: bool = True, block_types_to_format: Optional[Sequence[Type[ItemBlock]]] = None
) -> Tuple[str, str]:
    """Format the source and blocks of a dialog item. Helper function to use with Dialog.map()."""
    source_str = item.format_source(with_address=with_address)
    blocks_str = "\n\n".join(item.format_blocks(block_types_to_format=block_types_to_format))
    return source_str, blocks_str


class Dialog(BaseModel):
    """
    Represents the expected payload for an execute request.

    Attributes:
        items (list[DialogItem]): A list of DialogItem objects consisting of request/response from the user and agent.
    """

    items: Sequence[DialogItem]

    def map(self, func: DialogItemTransformer) -> List[Any]:
        """Apply a function to each item in the dialog."""
        return [func(item) for item in self.items]

    def format_as_markdown(self, indent: int = 1) -> str:
        """Formats the dialog as a markdown string with default parameters from `format_source_and_blocks`."""
        sources_and_blocks = self.map(format_source_and_blocks)
        return "\n\n".join(f"{'#' * indent} {source}\n\n{blocks}" for source, blocks in sources_and_blocks)

    # noinspection PyNestedDecorators
    @field_validator("items", mode="before")
    @classmethod
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
