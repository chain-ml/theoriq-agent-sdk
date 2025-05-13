from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Sequence

import yaml

from .data_object import DataObject, DataObjectSpecBase


class AgentUrls:
    def __init__(self, *, end_point: str, icon: str) -> None:
        self.end_point = end_point
        self.icon = icon

    @classmethod
    def undefined(cls) -> AgentUrls:
        return AgentUrls(end_point="", icon="")

    @classmethod
    def from_dict(cls, values: Mapping[str, Any]) -> AgentUrls:
        end_point = values.get("endPoint", "")
        icon = values.get("icon", "")
        return cls(end_point=end_point, icon=icon)

    def to_dict(self) -> Dict[str, Any]:
        return {"endPoint": self.end_point, "icon": self.icon}

    def __str__(self) -> str:
        return f"EndPoint: {self.end_point} - Icon: {self.icon}"


class AgentDescriptions:
    def __init__(self, *, short: str, long: str) -> None:
        self.short = short
        self.long = long

    @classmethod
    def from_dict(cls, values: Mapping[str, Any]) -> AgentDescriptions:
        short = values.get("short", "")
        long = values.get("long", "")
        return cls(short=short, long=long)

    def to_dict(self) -> Dict[str, Any]:
        return {"shortDescription": self.short, "longDescription": self.long}

    def __str__(self) -> str:
        return f"{self.short} - {self.long}"


class AgentMetadata:
    def __init__(
        self,
        name: str,
        descriptions: AgentDescriptions,
        tags: Sequence[str],
        examples: Sequence[str],
        cost_card: Optional[str],
    ) -> None:
        self.name = name  # duplicated with DataObjectMetadata.name; not really used
        self.descriptions = descriptions
        self.tags = tags
        self.examples = examples
        self.cost_card = cost_card

    @classmethod
    def from_dict(cls, values: Mapping[str, Any]) -> AgentMetadata:
        descriptions = AgentDescriptions.from_dict(values.get("descriptions", {}))
        tags = [value for value in values.get("tags", [])]
        examples = [value for value in values.get("examplePrompts", [])]
        cost_card = values.get("costCard")

        return AgentMetadata(name="", descriptions=descriptions, tags=tags, examples=examples, cost_card=cost_card)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "tags": self.tags,
            "examplePrompts": self.examples,
            "costCard": self.cost_card,
        }
        result |= {**self.descriptions.to_dict()}
        return result


class AgentSpec(DataObjectSpecBase):
    def __init__(self, metadata: AgentMetadata, urls: AgentUrls) -> None:
        self.metadata = metadata
        self.urls = urls

    @classmethod
    def from_dict(cls, values: Mapping[str, Any]) -> AgentSpec:
        metadata = AgentMetadata.from_dict(values)
        urls = AgentUrls.from_dict(values.get("urls", {}))
        return AgentSpec(metadata, urls=urls)

    def to_dict(self) -> Dict[str, Any]:
        result = self.metadata.to_dict()
        result |= {"imageUrl": self.urls.icon}
        return result


class AgentDataObject(DataObject[AgentSpec]):
    @classmethod
    def from_dict(cls, values: Dict[str, Any]) -> AgentDataObject:
        return super()._from_dict(AgentSpec, values)

    @classmethod
    def from_yaml(cls, filename: str) -> AgentDataObject:
        with open(filename, "r", encoding="utf-8") as f:
            values = yaml.safe_load(f)
            cls._check_kind(values, "TheoriqAgent")
            return AgentDataObject.from_dict(values)

    def to_payload(self, headers: Optional[Sequence[Dict[str, str]]] = None) -> Dict[str, Any]:
        # TODO: either delete or reframe AgentDataObject
        """
        Convert to payload expected by create agent endpoint.

        Args:
            headers (Optional[Sequence[Dict[str, str]]]): Optional headers to be added to the request,
                each header is a dictionary with `name` and `value`
        """
        return {
            "configuration": {
                "deployment": {
                    "headers": headers or [],
                    "url": self.spec.urls.end_point,
                },
            },
            "metadata": {
                "name": self.metadata.name,
                "shortDescription": self.spec.metadata.descriptions.short,
                "longDescription": self.spec.metadata.descriptions.long,
                "tags": self.spec.metadata.tags,
                "examplePrompts": self.spec.metadata.examples,
                "imageUrl": self.spec.urls.icon,
                "costCard": self.spec.metadata.cost_card,
            },
        }
