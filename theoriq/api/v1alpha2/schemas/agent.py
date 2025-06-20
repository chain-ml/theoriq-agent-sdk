from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel


class System(BaseModel):
    id: str
    public_key: str = Field(..., alias="publicKey")
    owner_address: str = Field(..., alias="ownerAddress")
    state: str
    metadata_hash: str = Field(..., alias="metadataHash")
    configuration_hash: str = Field(..., alias="configurationHash")
    tags: List[str]


class Metadata(BaseModel):
    name: str
    short_description: str = Field(..., alias="shortDescription")
    long_description: str = Field(..., alias="longDescription")
    tags: List[str]
    cost_card: Optional[str] = Field(None, alias="costCard")
    example_prompts: List[str] = Field(..., alias="examplePrompts")

    def format(self) -> str:
        parts = [
            f"Name: {self.name}",
            f"Short description: {self.short_description}",
            f"Long description: " f"{self.long_description}",
            f"Tags: {self.tags}",
            f"Example prompts: {self.example_prompts}",
        ]
        if self.cost_card is not None:
            parts.append(f"Cost card: {self.cost_card}")
        return "\n".join(parts)

    def format_with_id(self, id: str) -> str:
        return f"Agent address: {id}\n" + self.format()


class Virtual(BaseModel):
    agent_id: str = Field(..., alias="agentId")
    metadata_hash: str = Field(..., alias="metadataHash")
    configuration_hash: str = Field(..., alias="configurationHash")
    configuration: Dict[str, Any] = Field(..., alias="configuration")


class SupportedBlocks(BaseModel):
    input: List[str]
    output: List[str]


class Configuration(BaseModel):
    config_schema: Dict[str, Any] = Field(..., alias="schema")
    supported_blocks: SupportedBlocks = Field(..., alias="supportedBlocks")
    deployment: Optional[Dict[str, Any]] = None
    virtual: Optional[Virtual] = Field(default=None)

    @property
    def is_deployed(self) -> bool:
        return self.deployment is not None

    @property
    def is_virtual(self) -> bool:
        return self.virtual is not None

    @property
    def is_valid(self) -> bool:
        return self.is_deployed or self.is_virtual

    @property
    def is_empty(self) -> bool:
        return not self.is_deployed and not self.is_virtual

    @property
    def ensure_deployment(self) -> Dict[str, Any]:
        if self.deployment is None:
            raise RuntimeError("Deployment configuration is None")
        return self.deployment

    @property
    def ensure_virtual(self) -> Virtual:
        if self.virtual is None:
            raise RuntimeError("Virtual configuration is None")
        return self.virtual

    # noinspection PyNestedDecorators
    @field_validator("virtual", mode="before")
    @classmethod
    def validate_virtual(cls, value: Any) -> Optional[Any]:
        # Handle cases where `virtual` is an empty dict or None
        if value is None or value == {}:
            return None
        if isinstance(value, dict):
            return Virtual(**value)
        return value

    # noinspection PyNestedDecorators
    @field_validator("deployment", mode="before")
    @classmethod
    def validate_deployment(cls, value: Any) -> Optional[Any]:
        # Handle cases where `deployment` is an empty dict or None
        if value is None or value == {}:
            return None
        return value


class AgentResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    system: System
    metadata: Metadata
    configuration: Configuration

    def __repr__(self) -> str:
        return f"AgentResponse(id={self.system.id}, name={self.system.public_key})"

    def format(self) -> str:
        return self.metadata.format_with_id(self.system.id)
