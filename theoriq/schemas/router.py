from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

from .schemas import BaseData, ItemBlock


class RouteItem(BaseData):
    """ """

    def __init__(self, name: str, score: float, reason: Optional[str] = None) -> None:
        self.name = name
        self.score = score
        self.reason = reason

    def to_dict(self) -> Dict[str, Any]:
        result = {"name": self.name, "score": self.score}
        if self.reason is not None:
            result["reason"] = self.reason
        return result

    @classmethod
    def from_dict(cls, values: Dict[str, Any]) -> RouteItem:
        return cls(name=values["name"], score=values["score"], reason=values.get("reason"))

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

    @classmethod
    def is_valid(cls, block_type: str) -> bool:
        return block_type == RouterItemBlock.block_type()
