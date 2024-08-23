from __future__ import annotations

from typing import Any, Dict, Optional

from .schemas import BaseData, ItemBlock


class DataItem(BaseData):
    """ """

    def __init__(self, data: str) -> None:
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        return {"data": self.data}


class DataItemBlock(ItemBlock[DataItem]):
    """ """

    def __init__(self, *, data: str, data_type: Optional[str] = None) -> None:
        sub_type = f":{data_type}" if data_type is not None else ""
        super().__init__(bloc_type=f"{DataItemBlock.block_type()}{sub_type}", data=DataItem(data=data))

    @classmethod
    def from_dict(cls, data: Dict[str, Any], block_type: str) -> DataItemBlock:
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        return cls(data=data["data"], data_type=cls.sub_type(block_type))

    @classmethod
    def block_type(cls) -> str:
        return "data"

    @classmethod
    def is_valid(cls, block_type: str) -> bool:
        return block_type.startswith(DataItemBlock.block_type())
