from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Any, Optional, Iterable, Callable, Sequence, Annotated
from pydantic import BaseModel, field_validator, Field


from .items import RouterBlock, TextBlock, CodeBlock, MetricsBlock
from .bloc import BlockBase
from .web3.commands import CommandBlock
from ..types import SourceType

UnknownBlock = BlockBase[dict[str, Any], str]


# Main data model
class DialogItem(BaseModel):
    timestamp: datetime
    source_type: Annotated[SourceType, Field(alias="sourceType")]
    source: str
    blocks: List[BlockBase]

    @field_validator("source")
    def validate_source(cls, v):
        # Basic validation for hex string
        if not v.startswith("0x"):
            raise ValueError("Source must start with '0x'")
        return v

    def model_dump_json(self, **kwargs):
        """Override to ensure proper JSON serialization"""
        # Set default serialization options
        kwargs.setdefault("by_alias", True)
        kwargs.setdefault("exclude_none", True)
        kwargs.setdefault("exclude_defaults", True)
        kwargs.setdefault("exclude_unset", True)
        return super().model_dump_json(**kwargs)

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

    def find_blocks_of_type(self, block_type: str) -> Iterable[BlockBase]:

        for block in self.blocks:
            if block.block_type == block_type:
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


DialogItemPredicate = Callable[[DialogItem], bool]


# Factory function to parse blocks with unknown type handling
def parse_block(block_data: dict) -> BlockBase:
    """Parse a block dictionary into the appropriate Block type."""
    block_type = block_data.get("type", "")

    if block_type == "router":
        return RouterBlock(**block_data)
    elif block_type == "text" or block_type.startswith("text:"):
        return TextBlock(**block_data)
    elif block_type == "code" or block_type.startswith("code:"):
        return CodeBlock(**block_data)
    elif block_type == "metrics":
        return MetricsBlock(**block_data)
    elif block_type == "command":
        return CommandBlock(**block_data)
    else:
        # For unknown types, use UnknownBlock
        return UnknownBlock(block_type=block_type, data=block_data.get("data", {}))


class Dialog(BaseModel):
    items: List[DialogItem]

    def model_dump_json(self, **kwargs):
        """Override to ensure proper JSON serialization"""
        # Set default serialization options
        kwargs.setdefault("by_alias", True)
        kwargs.setdefault("exclude_none", True)
        kwargs.setdefault("exclude_defaults", True)
        kwargs.setdefault("exclude_unset", True)
        return super().model_dump_json(**kwargs)

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

    def format_as_markdown(self, indent: int = 1) -> str:
        """Formats the dialog as a markdown string with default parameters from `format_source_and_blocks`."""
        sources_and_blocks = self.map(format_source_and_blocks)
        return "\n\n".join(f"{'#' * indent} {source}\n\n{blocks}" for source, blocks in sources_and_blocks)