from __future__ import annotations

from typing import List

import yaml
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class AgentResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    address: str
    owner_address: str
    publicKey: str
    name: str
    short_description: str
    long_description: str
    tags: List[str]
    cost_card: str
    state: str
    example_prompts: List[str]
    created_by: str
    created_at: str
    last_modified_by: str
    last_modified_at: str

    def __str__(self):
        return f"AgentResponse(id={self.id}, name={self.name})"

    @classmethod
    def from_yaml(cls, filename: str) -> AgentResponse:
        with open(filename, "r", encoding="utf-8") as file:
            yaml_data = yaml.safe_load(file)

        return AgentResponse(**yaml_data)


class PublicKeyResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    public_key: str
    key_type: str
