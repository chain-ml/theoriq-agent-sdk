"""
schemas.py

This module contains the schemas used by the Theoriq endpoint.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, Sequence, Type, TypeVar, Union


class BaseData(ABC):
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass


T_Data = TypeVar("T_Data", bound=Union[BaseData, Sequence[BaseData]])


class ItemBlock(Generic[T_Data]):
    """ """

    def __init__(
        self, *, bloc_type: str, data: T_Data, key: Optional[str] = None, reference: Optional[str] = None
    ) -> None:
        self.bloc_type = bloc_type
        self.data = data
        self.key = key
        self.reference = reference

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"type": self.bloc_type}
        if isinstance(self.data, BaseData):
            result["data"] = self.data.to_dict()
        elif isinstance(self.data, Sequence):
            result["data"] = {"items": [d.to_dict() for d in self.data]}

        if self.key is not None:
            result["key"] = self.key
        if self.reference is not None:
            result["ref"] = self.reference
        return result

    @classmethod
    def is_valid(cls, block_type: str) -> bool:
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data: dict, block_type: str):
        raise NotImplementedError

    @classmethod
    def block_type(cls) -> str:
        raise NotImplementedError

    @staticmethod
    def raise_if_not_valid(*, block_type: str, expected: str) -> None:
        if not block_type.startswith(expected):
            raise ValueError(f"Data type must be subtype of {expected}, not {block_type}")

    @staticmethod
    def sub_type(bloc_type: str) -> str:
        parts = bloc_type.split(":", 1)
        return parts[1] if len(parts) > 1 else ""

    @staticmethod
    def root_type(bloc_type: str) -> str:
        return bloc_type.split(":", 1)[0]


def filter_blocks(blocks: Sequence[ItemBlock], block_type: Type[ItemBlock]) -> Sequence[ItemBlock]:
    return list(filter(lambda x: block_type.is_valid(x.block_type()), blocks))
