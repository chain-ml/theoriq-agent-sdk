from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Annotated, Any, Callable, Iterable, List, Optional, Sequence, Tuple, Type

from pydantic import Field, field_serializer, field_validator

from ..types import SourceType
from .block import AllBlocks, BaseData, BaseTheoriqModel, BlockBase, BlockBasePredicate, BlockOfType, BlockOfTypes
from .code_items import CodeBlock
from .command_items import CommandBlock
from .custom_items import CustomBlock
from .data_items import DataBlock
from .metrics_items import MetricsBlock
from .router_items import RouterBlock
from .suggestions_items import SuggestionsBlock
from .text_items import TextBlock
from .tool_items import ToolCallBlock, ToolCallResultBlock
from .web3_items import Web3ProposedTxBlock, Web3SignedTxBlock

UnknownBlock = BlockBase[dict[str, Any], str]


# Main data model
class DialogItem(BaseTheoriqModel):
    timestamp: datetime = Field(..., description="ISO format timestamp")
    source_type: Annotated[SourceType, Field(description="Source type, could be `user`, `agent`")]
    source: Annotated[str, Field(pattern="0x[a-fA-F0-9]{40}([a-fA-F0-9]{24})?", description="Address of the source")]
    blocks: List[BlockBase]

    @field_validator("timestamp", mode="before")
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

    @classmethod
    def _datetime_from_str(cls, value: str) -> datetime:
        try:
            if re.search(r"\.\d+Z$", value):
                value = value[: value.find(".") + 7] + "Z"
                result = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
            else:
                result = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            result = datetime.fromisoformat(value)
        return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result

    @field_validator("blocks", mode="before")
    def parse_blocks(cls, v):
        if isinstance(v, list):
            result = [DialogItem.parse_block(item) for item in v]
            return result
        return v

    @staticmethod
    def parse_block(v):
        if isinstance(v, dict):
            block_type_name = v.get("type")
            block_type = BlockBase.get_block_type(block_type_name)
            if block_type is not None:
                return block_type(**v)
            return UnknownBlock(**v)
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

    def find_blocks(self, predicate: BlockBasePredicate) -> Iterable[BlockBase]:
        for block in self.blocks:
            if predicate(block):
                yield block
        return

    def find_blocks_of_type(self, block_type: str) -> Iterable[BlockBase]:
        return self.find_blocks(BlockOfType(block_type))

    def has_blocks(self, predicate: BlockBasePredicate) -> bool:
        for block in self.blocks:
            if predicate(block):
                return True
        return False

    def has_blocks_of_type(self, block_type: str) -> bool:
        return self.has_blocks(BlockOfType(block_type))

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

        last_text_block = self.find_last_block_of_type("text")
        if last_text_block is None:
            raise RuntimeError("No text blocks found in the dialog item")

        return last_text_block.data.text

    def format_source(self, with_address: bool = True) -> str:
        """Format the string describing the creator of the dialog item."""
        source_type = self.source_type.value.capitalize()
        return source_type if not with_address else f"{source_type} ({self.source})"

    def format_blocks(self, block_to_format: BlockBasePredicate = AllBlocks) -> List[str]:
        """Format each block with `to_str()` whose satisfy `block_to_format` predicate."""
        return [block.to_str() for block in self.blocks if block_to_format(block)]


DialogItemPredicate = Callable[[DialogItem], bool]
DialogItemTransformer = Callable[[DialogItem], Any]


# Block type mapping for factory function
BlockBase.register(CodeBlock)
BlockBase.register(CommandBlock)
BlockBase.register(CustomBlock)
BlockBase.register(DataBlock)
BlockBase.register(MetricsBlock)
BlockBase.register(RouterBlock)
BlockBase.register(SuggestionsBlock)
BlockBase.register(TextBlock)
BlockBase.register(ToolCallBlock)
BlockBase.register(ToolCallResultBlock)
BlockBase.register(Web3ProposedTxBlock)
BlockBase.register(Web3SignedTxBlock)


def format_source_and_blocks(
    item: DialogItem, with_address: bool = True, block_types_to_format: Optional[Sequence[Type[BlockBase]]] = None
) -> Tuple[str, str]:
    """Format the source and blocks of a dialog item. Helper function to use with Dialog.map()."""
    source_str = item.format_source(with_address=with_address)

    predicate = BlockOfTypes(block_types_to_format) if block_types_to_format else AllBlocks
    blocks_str = "\n\n".join(item.format_blocks(block_to_format=predicate))
    return source_str, blocks_str


class Dialog(BaseData):
    items: List[DialogItem]

    def filter_items(self, predicate: DialogItemPredicate) -> List[DialogItem]:
        return [item for item in self.items if predicate(item)]

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

    def map(self, transformer: DialogItemTransformer) -> List[Any]:
        """Apply a function to each item in the dialog."""
        return [transformer(item) for item in self.items]

    def format_as_markdown(self, indent: int = 1) -> str:
        """Formats the dialog as a markdown string with default parameters from `format_source_and_blocks`."""
        sources_and_blocks = self.map(format_source_and_blocks)
        return "\n\n".join(f"{'#' * indent} {source}\n\n{blocks}" for source, blocks in sources_and_blocks)
