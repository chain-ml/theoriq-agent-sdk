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
    cost_card: str = Field(..., alias="costCard")
    example_prompts: List[str] = Field(..., alias="examplePrompts")


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

    @classmethod
    @field_validator("virtual", mode="before")
    def validate_virtual(cls, value: Any) -> Optional[Any]:
        # Handle cases where `b` is an empty dict or None
        if value is None or value == {}:
            return None
        if isinstance(value, dict):
            return Virtual(**value)
        return value


class AgentResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    system: System
    metadata: Metadata
    configuration: Configuration

    def __str__(self) -> str:
        return f"AgentResponse(id={self.system.id}, name={self.system.public_key})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AgentResponse):
            return False

        # state is different before and after minting
        return (
            self.system.id == other.system.id
            and self.system.public_key == other.system.public_key
            and self.system.owner_address == other.system.owner_address
            # and self.system.state == other.system.state
            and self.system.metadata_hash == other.system.metadata_hash
            and self.system.configuration_hash == other.system.configuration_hash
            and self.system.tags == other.system.tags
            and self.metadata.name == other.metadata.name
            and self.metadata.short_description == other.metadata.short_description
            and self.metadata.long_description == other.metadata.long_description
            and self.metadata.tags == other.metadata.tags
            and self.metadata.cost_card == other.metadata.cost_card
            and self.metadata.example_prompts == other.metadata.example_prompts
        )
