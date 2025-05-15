from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

import yaml
from pydantic import BaseModel, Field, model_validator

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


class AgentConfiguration(BaseModel):
    deployment: Optional[DeploymentConfiguration] = None
    virtual: Optional[VirtualConfiguration] = None

    @model_validator(mode="after")
    def validate_configuration(self) -> AgentConfiguration:
        if self.deployment is None and self.virtual is None:
            raise ValueError("At least one of deployment or virtual must be provided")
            # at least one or exactly one?

        return self

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)


class AgentMetadata(BaseModel):
    name: str
    short_description: str = Field(..., alias="shortDescription")
    long_description: str = Field(..., alias="longDescription")
    tags: List[str]
    example_prompts: List[str] = Field(..., alias="examplePrompts")
    cost_card: Optional[str] = Field(None, alias="costCard")
    image_url: Optional[str] = Field(None, alias="imageUrl")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True)


class AgentSpec(DataObjectSpecBase):
    def __init__(self, metadata: AgentMetadata, configuration: Optional[AgentConfiguration] = None) -> None:
        self._metadata = metadata
        self._configuration = configuration

    @property
    def metadata(self) -> AgentMetadata:
        return self._metadata

    @property
    def configuration(self) -> AgentConfiguration:
        if self._configuration is None:
            raise RuntimeError("AgentConfiguration is None")
        return self._configuration

    @property
    def maybe_configuration(self) -> Optional[AgentConfiguration]:
        return self._configuration

    @property
    def has_configuration(self) -> bool:
        return self.configuration is not None

    @classmethod
    def from_dict(cls, values: Mapping[str, Any]) -> AgentSpec:
        metadata = AgentMetadata.model_validate(values["metadata"])
        config_values = values.get("configuration")
        configuration = AgentConfiguration.model_validate(config_values) if config_values is not None else None
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
