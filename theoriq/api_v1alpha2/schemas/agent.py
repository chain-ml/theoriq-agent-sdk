from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field
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
    schema: Dict[str, Any]
    supported_blocks: SupportedBlocks = Field(..., alias="supportedBlocks")
    deployment: Optional[Dict[str, Any]] = None
    virtual: Optional[Virtual] = None


class AgentResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    system: System
    metadata: Metadata
    configuration: Configuration

    def __str__(self):
        return f"AgentResponse(id={self.system.id}, name={self.system.public_key})"
