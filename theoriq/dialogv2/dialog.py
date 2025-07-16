from datetime import datetime
from typing import List, Any, Optional
from pydantic import BaseModel, field_validator
from enum import Enum

from .items import RouterBlock, TextBlock, CodeBlock, MetricsBlock, BlockBase


class SourceType(str, Enum):
    USER = "user"
    SYSTEM = "system"
    AGENT = "agent"


UnknownBlock = BlockBase[dict[str, Any], str]


# Main data model
class DialogItem(BaseModel):
    timestamp: datetime
    sourceType: SourceType
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


# Factory function to parse blocks with unknown type handling
def parse_block(block_data: dict) -> BlockBase:
    """Parse a block dictionary into the appropriate Block type."""
    block_type = block_data.get("type", "")

    if block_type == "router":
        return RouterBlock(**block_data)
    elif block_type == "text" or block_type.startswith("text:"):
        return TextBlock(**block_data)
    elif block_type.startswith("code:"):
        return CodeBlock(**block_data)
    elif block_type == "metrics":
        return MetricsBlock(**block_data)
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