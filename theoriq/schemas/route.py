from __future__ import annotations

from typing import Any, Dict, Sequence

from .schemas import BaseData, ItemBlock


class RouteItem(BaseData):
    """ """

    def __init__(self, name: str, score: float):
        self.name = name
        self.score = score

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "score": self.score}

    @classmethod
    def from_dict(cls, values: Dict[str, Any]) -> RouteItem:
        return cls(name=values["name"], score=values["score"])

    def __str__(self):
        return f"RouteItem(name={self.name}, score={self.score})"


class RoutesItemBlock(ItemBlock[Sequence[RouteItem]]):
    """ """

    def __init__(self, routes: Sequence[RouteItem]):
        super().__init__(bloc_type="route", data=routes)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RoutesItemBlock:
        items = data.get("items", [])
        return cls(routes=[RouteItem.from_dict(route) for route in items])

    def best(self) -> RouteItem:
        return max(self.data, key=lambda obj: obj.score)
