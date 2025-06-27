from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Type

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from .data_object import DataObject, DataObjectSpecBase


class Header(BaseModel):
    name: str
    value: str


class DeploymentConfiguration(BaseModel):
    headers: List[Header] = Field(default_factory=list)
    url: str


class VirtualConfiguration(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    agent_id: str
    configuration: Dict[str, Any]

    def validate_schema(self, schema: Type[BaseModel]) -> None:
        """Ensure the configuration is valid against the given schema and update the configuration field."""
        self.configuration = schema.model_validate(self.configuration).model_dump()


class AgentConfiguration(BaseModel):
    deployment: Optional[DeploymentConfiguration] = None
    virtual: Optional[VirtualConfiguration] = None

    @classmethod
    def for_deployed(cls, url: str, headers: Optional[List[Header]] = None) -> AgentConfiguration:
        """Build a new configuration for a deployed agent."""
        return cls(deployment=DeploymentConfiguration(url=url, headers=headers or []), virtual=None)

    @classmethod
    def for_virtual(cls, agent_id: str, configuration: Dict[str, Any]) -> AgentConfiguration:
        """Build a new configuration for a virtual agent."""
        return cls(deployment=None, virtual=VirtualConfiguration(agent_id=agent_id, configuration=configuration))

    @property
    def ensure_deployment(self) -> DeploymentConfiguration:
        if self.deployment is None:
            raise RuntimeError("DeploymentConfiguration is None")
        return self.deployment

    @property
    def ensure_virtual(self) -> VirtualConfiguration:
        if self.virtual is None:
            raise RuntimeError("VirtualConfiguration is None")
        return self.virtual

    @model_validator(mode="after")
    def validate_configuration(self) -> AgentConfiguration:
        both_are_none = self.deployment is None and self.virtual is None
        both_are_not_none = self.deployment is not None and self.virtual is not None
        if both_are_none or both_are_not_none:
            raise ValueError("Exactly one of deployment or virtual must be provided")

        return self

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)


class AgentMetadata(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str
    short_description: str
    long_description: str
    tags: List[str] = Field(default_factory=list)
    example_prompts: List[str] = Field(default_factory=list)
    cost_card: Optional[str] = None
    image_url: Optional[str] = None

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
        result: Dict[str, Any] = {"metadata": self.metadata.to_dict()}
        if self.has_configuration:
            result["configuration"] = self.configuration.to_dict()
        return result


class AgentDataObject(DataObject[AgentSpec]):
    @classmethod
    def from_dict(cls, values: Dict[str, Any]) -> AgentDataObject:
        return super()._from_dict(AgentSpec, values)

    @classmethod
    def from_yaml(
        cls, filename: str, virtual_configuration_schema: Optional[Type[BaseModel]] = None
    ) -> AgentDataObject:
        with open(filename, "r", encoding="utf-8") as f:
            values = yaml.safe_load(f)
        cls._check_kind(values, "TheoriqAgent")
        data_object = AgentDataObject.from_dict(values)
        if virtual_configuration_schema is not None:
            data_object.spec.configuration.ensure_virtual.validate_schema(virtual_configuration_schema)
        return data_object
