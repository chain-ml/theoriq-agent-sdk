from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

import yaml
from pydantic import BaseModel, Field

from .data_object import DataObject, DataObjectSpecBase


class Header(BaseModel):
    name: str
    value: str


class DeploymentConfiguration(BaseModel):
    headers: List[Header]
    url: str


class VirtualConfiguration(BaseModel):
    agent_id: str = Field(..., alias="agentId")
    configuration: Dict[str, Any]


class AgentConfiguration:
    def __init__(
        self,
        deployment: Optional[DeploymentConfiguration] = None,
        virtual: Optional[VirtualConfiguration] = None,
    ) -> None:
        if deployment is None and virtual is None:
            raise ValueError("At least one of deployment or virtual must be provided")
            # at least one or exactly one?

        self.deployment = deployment
        self.virtual = virtual

    @classmethod
    def from_dict(cls, values: Dict[str, Any]) -> AgentConfiguration:
        deployment_values = values.get("deployment")
        virtual_values = values.get("virtual")
        deployment = (
            DeploymentConfiguration.model_validate(deployment_values) if deployment_values is not None else None
        )
        virtual = VirtualConfiguration.model_validate(virtual_values) if virtual_values is not None else None
        return cls(deployment=deployment, virtual=virtual)

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.deployment is not None:
            result["deployment"] = self.deployment.model_dump()
        if self.virtual is not None:
            result["virtual"] = self.virtual.model_dump(by_alias=True)
        return result


class AgentMetadata:
    def __init__(
        self,
        name: str,
        short_description: str,
        long_description: str,
        tags: List[str],
        example_prompts: List[str],
        cost_card: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> None:
        self.name = name
        self.short_description = short_description
        self.long_description = long_description
        self.tags = tags
        self.example_prompts = example_prompts
        self.cost_card = cost_card
        self.image_url = image_url

    @classmethod
    def from_dict(cls, values: Dict[str, Any]) -> AgentMetadata:
        name = values["name"]
        short_description = values["shortDescription"]
        long_description = values["longDescription"]
        tags = values.get("tags", [])
        example_prompts = values.get("examplePrompts", [])
        cost_card = values.get("costCard")
        image_url = values.get("imageUrl")

        return cls(
            name=name,
            short_description=short_description,
            long_description=long_description,
            tags=tags,
            example_prompts=example_prompts,
            cost_card=cost_card,
            image_url=image_url,
        )

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "name": self.name,
            "shortDescription": self.short_description,
            "longDescription": self.long_description,
            "tags": self.tags,
            "examplePrompts": self.example_prompts,
        }
        if self.cost_card is not None:
            result["costCard"] = self.cost_card
        if self.image_url is not None:
            result["imageUrl"] = self.image_url

        return result


class AgentSpec(DataObjectSpecBase):
    def __init__(self, metadata: AgentMetadata, configuration: Optional[AgentConfiguration] = None) -> None:
        self.metadata = metadata
        self.configuration = configuration

    @property
    def has_configuration(self) -> bool:
        return self.configuration is not None

    @property
    def ensure_configuration(self) -> AgentConfiguration:
        if self.configuration is None:
            raise RuntimeError("Called ensure_configuration() but configuration is None")
        return self.configuration

    @classmethod
    def from_dict(cls, values: Mapping[str, Any]) -> AgentSpec:
        metadata = AgentMetadata.from_dict(values["metadata"])
        config_values = values.get("configuration")
        configuration = AgentConfiguration.from_dict(config_values) if config_values is not None else None
        return AgentSpec(metadata=metadata, configuration=configuration)

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        if self.metadata is not None:
            result["metadata"] = self.metadata.to_dict()
        if self.configuration is not None:
            result["configuration"] = self.configuration.to_dict()
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
