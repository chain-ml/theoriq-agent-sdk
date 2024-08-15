from __future__ import annotations
from typing import Any, Dict, List, Mapping, Optional, Sequence

import yaml
from .data_object import DataObjectSpecBase, DataObject


class AgentUrls:
    def __init__(self, *, end_point: str, icon: str) -> None:
        self.end_point = end_point
        self.icon = icon

    @classmethod
    def from_dict(cls, values: Mapping[str, Any]) -> AgentUrls:
        end_point = values.get("endPoint", "")
        icon = values.get("icon", end_point + "system/icon.png" if end_point else "")
        return cls(end_point=end_point, icon=icon)

    def to_dict(self) -> Dict[str, Any]:
        return {"endPoint": self.end_point, "icon": self.icon}

    def __str__(self):
        return f"EndPoint: {self.end_point} - Icon: {self.icon}"


class AgentDesciptions:
    def __init__(self, *, short: str, long: str) -> None:
        self.short = short
        self.long = long

    @classmethod
    def from_dict(cls, values: Mapping[str, Any]) -> AgentDesciptions:
        short = values.get("short", "")
        long = values.get("long", "")
        return cls(short=short, long=long)

    def to_dict(self) -> Dict[str, Any]:
        return {"shortDesciption": self.short, "longDesciption": self.long}

    def __str__(self):
        return f"{self.short} - {self.long}"


class AgentSpec(DataObjectSpecBase):
    def __init__(
        self,
        urls: AgentUrls,
        descriptions: AgentDesciptions,
        tags: Sequence[str],
        examples: Sequence[str],
        cost_card: str,
    ) -> None:
        self.urls = urls
        self.descriptions = descriptions
        self.tags = tags
        self.examples = examples
        self.cost_card = cost_card

    @classmethod
    def from_dict(cls, values: Mapping[str, Any]) -> AgentSpec:
        urls = AgentUrls.from_dict(values.get("urls", {}))
        tags = [value for value in values.get("tags", [])]
        descriptions = AgentDesciptions.from_dict(values.get("descriptions", {}))
        examples = [value for value in values.get("examplePrompts", [])]
        cost_card = values.get("costCard", "")

        return AgentSpec(urls, descriptions, tags, examples, cost_card)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "tags": self.tags,
            "examplePrompts": self.examples,
            "costCard": self.cost_card,
        }
        result |= {**self.descriptions.to_dict()}
        result |= {"imageUrl": self.urls.icon}
        return result


class AgentDataObject(DataObject[AgentSpec]):
    """ """

    @classmethod
    def from_dict(cls, values: Dict[str, Any]) -> AgentDataObject:
        return super()._from_dict(AgentSpec, values)

    @classmethod
    def from_yaml(cls, filename: str) -> AgentDataObject:
        with open(filename, "r", encoding="utf-8") as f:
            values = yaml.safe_load(f)
            cls._check_kind(values, "TheoriqAgent")
            return AgentDataObject.from_dict(values)
