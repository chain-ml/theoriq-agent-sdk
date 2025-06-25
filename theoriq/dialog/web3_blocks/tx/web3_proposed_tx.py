from __future__ import annotations

from typing import Any, Dict, Optional

from theoriq.dialog import BaseData, ItemBlock


class Web3ProposedTxItem(BaseData):
    def __init__(
        self,
        *,
        abi: Dict[str, Any],
        description: str,
        known_addresses: Dict[str, str],
        tx_chain_id: int,
        tx_to: str,
        tx_gas_limit: str,
        tx_data: str,
        tx_nonce: int,
    ) -> None:
        self.abi = abi
        self.description = description
        self.known_addresses = known_addresses
        self.tx_chain_id = tx_chain_id
        self.tx_to = tx_to
        self.tx_gas_limit = tx_gas_limit
        self.tx_data = tx_data
        self.tx_nonce = tx_nonce

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Web3ProposedTxItem:
        return cls(
            abi=data["abi"],
            description=data["description"],
            known_addresses=data["knownAddresses"],
            tx_chain_id=data["txChainId"],
            tx_to=data["txTo"],
            tx_gas_limit=data["txGasLimit"],
            tx_data=data["txData"],
            tx_nonce=data["txNonce"],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "abi": self.abi,
            "description": self.description,
            "knownAddresses": self.known_addresses,
            "txChainId": self.tx_chain_id,
            "txTo": self.tx_to,
            "txGasLimit": self.tx_gas_limit,
            "txData": self.tx_data,
            "txNonce": self.tx_nonce,
        }

    def to_str(self) -> str:
        return f"Transaction: {self.description}"

    def __str__(self) -> str:
        return f"Web3ProposedTxItem({self.description})"


class Web3ProposedTxBlock(ItemBlock[Web3ProposedTxItem]):
    def __init__(self, *, item: Web3ProposedTxItem, key: Optional[str] = None, reference: Optional[str] = None) -> None:
        super().__init__(block_type=self.block_type(), data=item, key=key, reference=reference)

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], block_type: str, block_key: Optional[str] = None, block_ref: Optional[str] = None
    ) -> Web3ProposedTxBlock:
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        return cls(item=Web3ProposedTxItem.from_dict(data), key=block_key, reference=block_ref)

    @staticmethod
    def block_type() -> str:
        return "web3:proposedTx"

    @staticmethod
    def is_valid(block_type: str) -> bool:
        return block_type == Web3ProposedTxBlock.block_type()
