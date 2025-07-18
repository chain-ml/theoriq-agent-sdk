from __future__ import annotations

import re
from datetime import datetime, timezone
from itertools import tee
from typing import Annotated, Any, Callable, Iterable, List, Optional, Sequence, Tuple, Type

from pydantic import BaseModel, Field, field_serializer, field_validator

from ..types import SourceType
from .block import BlockBase
from .commands import CommandBlock
from .items import CodeBlock, MetricsBlock, RouterBlock, TextBlock, Web3ProposedTxBlock, Web3SignedTxBlock

UnknownBlock = BlockBase[dict[str, Any], str]


# Main data model
class DialogItem(BaseModel):
    timestamp: datetime = Field(..., description="ISO format timestamp")
    source_type: Annotated[SourceType, Field(alias="sourceType")]
    source: str
    blocks: List[BlockBase]

    @field_validator("timestamp", mode="before")
    @classmethod
    def validate_timestamp(cls, v):
        if isinstance(v, str):
            return cls._datetime_from_str(v)
        return v

    @field_validator("source")
    def validate_source(cls, v):
        # Basic validation for hex string
        if not v.startswith("0x"):
            raise ValueError("Source must start with '0x'")
        return v

    @field_serializer("timestamp")
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()

    class Config:
        populate_by_name = True

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

    def _set_dump_defaults(self, kwargs):
        """Set default serialization options"""
        kwargs.setdefault("by_alias", True)
        kwargs.setdefault("exclude_none", True)
        kwargs.setdefault("exclude_defaults", True)
        kwargs.setdefault("exclude_unset", True)
        return kwargs

    def model_dump_json(self, **kwargs):
        """Override to ensure proper JSON serialization"""
        return super().model_dump_json(**self._set_dump_defaults(kwargs))

    def model_dump(self, **kwargs):
        """Override to ensure proper JSON serialization"""
        return super().model_dump(**self._set_dump_defaults(kwargs))

    @field_validator("blocks", mode="before")
    def parse_blocks(cls, v):
        if isinstance(v, list):
            return [parse_block(block) if isinstance(block, dict) else block for block in v]
        return v

    @classmethod
    def new(cls, source: str, blocks: Sequence[BlockBase]) -> DialogItem:
        """Create a new instance with current datetime, deriving `source_type` from `source`."""
        return cls(
            timestamp=datetime.now(timezone.utc),
            source_type=SourceType.from_address(source),
            source=source,
            blocks=list(blocks),
        )

    @classmethod
    def new_text(cls, source: str, text: str) -> DialogItem:
        return DialogItem.new(source=source, blocks=[TextBlock.from_text(text=text)])

    def find_blocks_of_type(self, block_type: str) -> Iterable[BlockBase]:
        for block in self.blocks:
            if block.is_of_type(block_type):
                yield block
        return

    def has_blocks_of_type(self, block_type: str) -> bool:
        iterable = self.find_blocks_of_type(block_type)
        a, _ = tee(iterable)
        try:
            next(a)
            return True
        except StopIteration:
            return False

    def find_all_blocks_of_type(self, block_type: str) -> List[BlockBase]:
        return list(self.find_blocks_of_type(block_type))

    def find_first_block_of_type(self, block_type: str) -> Optional[BlockBase]:
        return next(iter(self.find_blocks_of_type(block_type)), None)

    def find_last_block_of_type(self, block_type: str) -> Optional[BlockBase]:
        last_item = None
        for last_item in self.find_blocks_of_type(block_type):  # fall back to iteration
            pass
        return last_item

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

    def format_blocks(self, block_types_to_format: Optional[Sequence[Type[BlockBase]]] = None) -> List[str]:
        """
        Format each block with `to_str()` whose type is in `block_types_to_format`.
        If `block_types_to_format` is None, format every block.
        """

        if block_types_to_format is None:
            return [block.data.to_str() for block in self.blocks]

        return [
            block.data.to_str()
            for block in self.blocks
            if any(isinstance(block, block_type) for block_type in block_types_to_format)
        ]


DialogItemPredicate = Callable[[DialogItem], bool]
DialogItemTransformer = Callable[[DialogItem], Any]


# Block type mapping for factory function
BLOCK_TYPE_MAP = {
    "router": RouterBlock,
    "text": TextBlock,
    "code": CodeBlock,
    "metrics": MetricsBlock,
    "command": CommandBlock,
    "web3:proposedTx": Web3ProposedTxBlock,
    "web3:signedTx": Web3SignedTxBlock,
}


# Factory function to parse blocks with unknown type handling
def parse_block(block_data: dict) -> BlockBase:
    """Parse a block dictionary into the appropriate Block type."""
    block_type = block_data.get("type", "")

    # Check exact match first
    if block_type in BLOCK_TYPE_MAP:
        return BLOCK_TYPE_MAP[block_type](**block_data)

    # Check for prefix matches
    if block_type.startswith("text:"):
        return TextBlock(**block_data)
    elif block_type.startswith("code:"):
        return CodeBlock(**block_data)

    # For unknown types, use UnknownBlock
    return UnknownBlock(block_type=block_type, data=block_data.get("data", {}))


def format_source_and_blocks(
    item: DialogItem, with_address: bool = True, block_types_to_format: Optional[Sequence[Type[BlockBase]]] = None
) -> Tuple[str, str]:
    """Format the source and blocks of a dialog item. Helper function to use with Dialog.map()."""
    source_str = item.format_source(with_address=with_address)
    blocks_str = "\n\n".join(item.format_blocks(block_types_to_format=block_types_to_format))
    return source_str, blocks_str


class Dialog(BaseModel):
    items: List[DialogItem]

    @property
    def last_item(self) -> Optional[DialogItem]:
        """
        Returns the last dialog item contained in the request based on the timestamp.

        Returns:
            Optional[DialogItem]: The dialog item with the most recent timestamp, or None if there are no items.
        """
        if len(self.items) == 0:
            return None

        return max(self.items, key=lambda obj: obj.timestamp)

    @property
    def last_text(self) -> str:
        """
        Returns the last text item from the dialog.

        Returns:
            str: The last text item from the dialog.

        Raises:
            RuntimeError: If the dialog is empty or no text blocks are found in the last dialog item.
        """
        last_item = self.last_item
        if last_item is None:
            raise RuntimeError("Got empty dialog")

        return last_item.extract_last_text()

    def last_item_from(self, source_type: SourceType) -> Optional[DialogItem]:
        """
        Returns the last dialog item from a specific source type based on the timestamp.

        Args:
            source_type (SourceType): The source type to filter the dialog items.

        Returns:
            Optional[DialogItem]: The dialog item with the most recent timestamp from the specified source type,
                                  or None if no items match the source type.
        """

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

        items = (item for item in self.items if predicate(item))
        return max(items, key=lambda obj: obj.timestamp) if items else None

    def map(self, func: DialogItemTransformer) -> List[Any]:
        """Apply a function to each item in the dialog."""
        return [func(item) for item in self.items]

    def format_as_markdown(self, indent: int = 1) -> str:
        """Formats the dialog as a markdown string with default parameters from `format_source_and_blocks`."""
        sources_and_blocks = self.map(format_source_and_blocks)
        return "\n\n".join(f"{'#' * indent} {source}\n\n{blocks}" for source, blocks in sources_and_blocks)
