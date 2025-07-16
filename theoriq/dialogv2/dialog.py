from datetime import datetime
from typing import Annotated, Generic, List, Optional, TypeVar, Union, Literal, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum

from typing_extensions import Self


class SourceType(str, Enum):
    USER = "user"
    SYSTEM = "system"
    AGENT = "agent"

T_Data = TypeVar("T_Data", bound=BaseModel)

class BlockBase(BaseModel, Generic[T_Data]):
    ref: Annotated[Optional[str], Field(default=None)]
    key: Annotated[Optional[str], Field(default=None)]
    type: str
    data: T_Data

    def model_dump_json(self, **kwargs):
        """Override to ensure proper JSON serialization"""
        # Set default serialization options
        kwargs.setdefault('by_alias', True)
        kwargs.setdefault('exclude_none', True)
        kwargs.setdefault('exclude_defaults', True)
        kwargs.setdefault('exclude_unset', True)
        return super().model_dump_json(**kwargs)


# Router Block Data Models
class RouterItem(BaseModel):
    name: str
    score: float
    reason: Optional[str] = None


class RouterData(BaseModel):
    items: List[RouterItem]


# Text Block Data Model
class TextData(BaseModel):
    text: str


# Code Block Data Model
class CodeData(BaseModel):
    code: str


# Metrics Block Data Models
class MetricItem(BaseModel):
    name: str
    value: float
    trendPercentage: float


class MetricsData(BaseModel):
    items: List[MetricItem]


# Block Models
class RouterBlock(BlockBase[RouterData]):
    pass
    # type: Literal["router"]
    # data: RouterData


class TextBlock(BlockBase[TextData]):
    # type: str
    # data: TextData

    @staticmethod
    def from_text(text: str, type: Optional[Literal["text"]] = "text") -> Self:
        return TextBlock(type=type, data=TextData(text=text), ref=None, key=None)

class CodeBlock(BlockBase[CodeData]):
    pass
    # type: str  # This will match patterns like "code:python", "code:javascript", etc.
    # data: CodeData

    # @field_validator('type')
    # def validate_code_type(cls, v):
    #     if not v.startswith("code:"):
    #         raise ValueError("Code block type must start with 'code:'")
    #     return v


class MetricsBlock(BlockBase[MetricsData]):
    pass
    # type: Literal["metrics"]
    # data: MetricsData


class UnknownBlock(BlockBase[dict[str, Any]]):
    pass
    # type: str
    # data: dict[str, Any] = Field(default_factory=dict)


# Union type for all possible blocks
Block = Union[RouterBlock, TextBlock, CodeBlock, MetricsBlock, UnknownBlock]


# Main data model
class DialogItem(BaseModel):
    timestamp: datetime
    sourceType: SourceType
    source: str
    blocks: List[Block]

    @field_validator('source')
    def validate_source(cls, v):
        # Basic validation for hex string
        if not v.startswith("0x"):
            raise ValueError("Source must start with '0x'")
        return v

    def model_dump_json(self, **kwargs):
        """Override to ensure proper JSON serialization"""
        # Set default serialization options
        kwargs.setdefault('by_alias', True)
        kwargs.setdefault('exclude_none', True)
        kwargs.setdefault('exclude_defaults', True)
        kwargs.setdefault('exclude_unset', True)
        return super().model_dump_json(**kwargs)

    @field_validator('blocks', mode='before')
    def parse_blocks(cls, v):
        if isinstance(v, list):
            return [parse_block(block) if isinstance(block, dict) else block for block in v]
        return v

# Factory function to parse blocks with unknown type handling
def parse_block(block_data: dict) -> Block:
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
        return UnknownBlock(
            type=block_type,
            data=block_data.get("data", {})
        )

class Dialog(BaseModel):
    items: List[DialogItem]

    def model_dump_json(self, **kwargs):
        """Override to ensure proper JSON serialization"""
        # Set default serialization options
        kwargs.setdefault('by_alias', True)
        kwargs.setdefault('exclude_none', True)
        kwargs.setdefault('exclude_defaults', True)
        kwargs.setdefault('exclude_unset', True)
        return super().model_dump_json(**kwargs)
