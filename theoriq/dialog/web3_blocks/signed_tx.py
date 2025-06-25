from __future__ import annotations

from typing import Any, Dict, Optional

from theoriq.dialog import BaseData, ItemBlock


class Web3SignedTxItem(BaseData):
    def __init__(self, *, chain_id: int, tx_hash: str) -> None:
        self.chain_id = chain_id
        self.tx_hash = tx_hash

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Web3SignedTxItem:
        return cls(chain_id=int(data["chainId"]), tx_hash=data["txHash"])

    def to_dict(self) -> Dict[str, Any]:
        return {"chainId": self.chain_id, "txHash": self.tx_hash}

    def to_str(self) -> str:
        return f"Transaction hash: `{self.tx_hash}` on chain `{self.chain_id}`"

    def __str__(self) -> str:
        return f"Web3SignedTxItem(chainId={self.chain_id}, txHash={self.tx_hash})"


class Web3SignedTxBlock(ItemBlock[Web3SignedTxItem]):
    def __init__(self, *, item: Web3SignedTxItem, key: Optional[str] = None, reference: Optional[str] = None) -> None:
        super().__init__(block_type=self.block_type(), data=item, key=key, reference=reference)

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], block_type: str, block_key: Optional[str] = None, block_ref: Optional[str] = None
    ) -> Web3SignedTxBlock:
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        return cls(item=Web3SignedTxItem.from_dict(data), key=block_key, reference=block_ref)

    @staticmethod
    def block_type() -> str:
        return "web3:signedTx"

    @staticmethod
    def is_valid(block_type: str) -> bool:
        return block_type == Web3SignedTxBlock.block_type()
