from __future__ import annotations
from typing import Optional, List, Literal, Any, Dict, Annotated

from pydantic import BaseModel, field_validator, model_validator, Field

from .bloc import BlockBase


class CodeData(BaseModel):
    code: str
    language: Optional[str] = None

    def to_str(self) -> str:
        if self.language:
            result = [f"```{self.language}", self.code, "```"]
        else:
            result = [f"```", self.code, "```"]
        return "\n".join(result)

    def __str__(self) -> str:
        """
        Returns a string representation of the CodeItem instance.

        Returns:
            str: A string representing the CodeItem.
        """
        return f"CodeItem(code={self.code}, language={self.language})"


class CodeBlock(BlockBase[CodeData, Annotated[str, Field(pattern="code(:.*)?")]]):
    @field_validator("block_type")
    def validate_block_type(cls, v):
        if not v.startswith("code"):
            raise ValueError('CodeBlock block_type must start with "code"')
        return v

    @model_validator(mode="after")
    def set_language_from_block_type(self):
        if self.data and not self.data.language:
            language = self.sub_type(self.block_type)
            if language:
                self.data.language = language
        return self

    @classmethod
    def from_code(cls, code: str, language: Optional[str] = None) -> CodeBlock:
        block_type = f"code:{language}" if language else "code"
        return cls(block_type=block_type, data=CodeData(code=code, language=language))


class MetricItem(BaseModel):
    name: str
    value: float
    trend_percentage: Annotated[float, Field(alias="trendPercentage")]


class MetricsData(BaseModel):
    items: List[MetricItem]


class RouterItem(BaseModel):
    name: str
    score: float
    reason: Optional[str] = None


class RouterData(BaseModel):
    items: List[RouterItem]


class RouterBlock(BlockBase[RouterData, Literal["router"]]):
    pass


class TextData(BaseModel):
    text: str
    type: Optional[str] = None

    def to_str(self) -> str:
        if self.type is None:
            return self.text
        result = [f"```{self.type}", self.text, "```"]
        return "\n".join(result)

    def __str__(self) -> str:
        """
        Returns a string representation of the TextItem instance.

        Returns:
            str: A string representing the TextItem.
        """
        return f"TextItem(text={self.text}, type={self.type})"


class TextBlock(BlockBase[TextData, Annotated[str, Field(pattern="text(:.*)?")]]):
    @field_validator("block_type")
    def validate_block_type(cls, v):
        if not v.startswith("text"):
            raise ValueError('TextBlock block_type must start with "text"')
        return v

    @model_validator(mode="after")
    def set_text_type_from_block_type(self):
        if self.data and not self.data.type:
            type = self.sub_type(self.block_type)
            if type:
                self.data.type = type
        return self

    @classmethod
    def from_text(cls, text: str, block_type: Literal["text"] = "text") -> TextBlock:
        return TextBlock(block_type=block_type, data=TextData(text=text))


class MetricsBlock(BlockBase[MetricsData, Literal["metrics"]]):
    pass


class Web3ProposedTxData(BaseModel):
    abi: Dict[str, Any]
    description: str
    known_addresses: Dict[str, str]
    tx_chain_id: int
    tx_to: str
    tx_gas_limit: str
    tx_data: str
    tx_nonce: int


class Web3ProposedTxBlock(BlockBase[Web3ProposedTxData, Literal["web3:proposedTx"]]):
    pass


class Web3SignedTxData(BaseModel):
    chain_id: int
    tx_hash: str


class Web3SignedTxBlock(BlockBase[Web3SignedTxData, Literal["web3:signedTx"]]):
    pass
