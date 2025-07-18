from __future__ import annotations

from typing import Annotated, Any, Dict, Literal
from typing_extensions import Self

from pydantic import Field

from .block import BaseData, BlockBase


class Web3ProposedTxData(BaseData):
    abi: Dict[str, Any]
    description: str
    known_addresses: Annotated[Dict[str, str], Field(...)]
    tx_chain_id: Annotated[int, Field(..., gt=0, description="Chain ID of the transaction")]
    tx_to: Annotated[str, Field(..., pattern="0x[a-fA-F0-9]{40}", description="Address of the transaction to")]
    tx_gas_limit: Annotated[int, Field(..., ge=0, description="Gas limit for the transaction")]
    tx_data: Annotated[str, Field(..., description="Data for the transaction")]
    tx_nonce: Annotated[int, Field(..., ge=0, description="Nonce for the transaction")]


class Web3ProposedTxBlock(BlockBase[Web3ProposedTxData, Literal["web3:proposedTx"]]):
    pass


class Web3SignedTxData(BaseData):
    chain_id: Annotated[int, Field(..., gt=0, description="Chain ID of the transaction")]
    tx_hash: Annotated[str, Field(pattern="0x[a-fA-F0-9]{64}", description="Transaction hash in hex format")]
    status: Annotated[Literal[0, 1], Field(description="Transaction status: 0 for failure, 1 for success")]

    @classmethod
    def from_success(cls, chain_id: int, tx_hash: str) -> Self:
        return cls(chain_id=chain_id, tx_hash=tx_hash, status=1)

    @classmethod
    def from_failure(cls, chain_id: int, tx_hash: str) -> Self:
        return cls(chain_id=chain_id, tx_hash=tx_hash, status=0)


class Web3SignedTxBlock(BlockBase[Web3SignedTxData, Literal["web3:signedTx"]]):
    pass
