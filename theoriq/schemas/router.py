from __future__ import annotations

from typing import Any, Dict, Sequence

from .schemas import BaseData, ItemBlock


class RouteItem(BaseData):
    """ """

    def __init__(self, name: str, score: float) -> None:
        self.name = name
        self.score = score

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "score": self.score}

    @classmethod
    def from_dict(cls, values: Dict[str, Any]) -> RouteItem:
        return cls(name=values["name"], score=values["score"])

    def __str__(self):
        return f"RouteItem(name={self.name}, score={self.score})"


class RouterItemBlock(ItemBlock[Sequence[RouteItem]]):
    """ """

    def __init__(self, routes: Sequence[RouteItem]) -> None:
        super().__init__(bloc_type=RouterItemBlock.block_type(), data=routes)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], block_type: str) -> RouterItemBlock:
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        items = data.get("items", [])
        return cls(routes=[RouteItem.from_dict(route) for route in items])

    def best(self) -> RouteItem:
        return max(self.data, key=lambda obj: obj.score)

    @staticmethod
    def block_type() -> str:
        return "router"

    @staticmethod
    def is_valid(block_type: str) -> bool:
        return block_type == RouterItemBlock.block_type()
