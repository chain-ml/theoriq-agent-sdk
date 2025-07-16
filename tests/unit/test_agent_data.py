import os.path
from typing import Final

import pytest
from pydantic import BaseModel, ValidationError, field_validator
from tests import DATA_DIR, OsEnviron

from theoriq.biscuit import AgentAddress
from theoriq.types import (
    AgentConfiguration,
    AgentDataObject,
    AgentMetadata,
    DeploymentConfiguration,
    Header,
    VirtualConfiguration,
)
from theoriq.utils import MissingEnvVariableException

RANDOM_AGENT_ID: Final[str] = str(AgentAddress.random())


def test_metadata_camel_snake_case() -> None:
    metadata_snake = AgentMetadata(
        name="Test Agent",
        short_description="Short description",
        long_description="Long description",
        tags=["tag"],
        example_prompts=["prompt"],
        cost_card="Free",
        image_url="http://example.com/image.jpg",
    )

    metadata_camel = AgentMetadata(
        **{  # type: ignore
            "name": "Test Agent",
            "shortDescription": "Short description",
            "longDescription": "Long description",
            "tags": ["tag"],
            "examplePrompts": ["prompt"],
            "costCard": "Free",
            "imageUrl": "http://example.com/image.jpg",
        }
    )

    assert metadata_snake == metadata_camel

    assert metadata_snake.to_dict() == metadata_camel.to_dict()
    assert all("_" not in key for key in metadata_snake.to_dict().keys())


def test_agent_configuration() -> None:
    config = AgentConfiguration(deployment=DeploymentConfiguration(url="http://example.com"))

    dict_output = config.to_dict()
    assert "deployment" in dict_output
    assert "virtual" not in dict_output
    assert dict_output["deployment"]["url"] == "http://example.com"
    assert len(dict_output["deployment"]["headers"]) == 0

    config = AgentConfiguration(
        deployment=DeploymentConfiguration(headers=[Header(name="test", value="value")], url="http://example.com")
    )

    dict_output = config.to_dict()
    assert "deployment" in dict_output
    assert "virtual" not in dict_output
    assert dict_output["deployment"]["url"] == "http://example.com"
    assert len(dict_output["deployment"]["headers"]) == 1
    assert dict_output["deployment"]["headers"][0]["name"] == "test"
    assert dict_output["deployment"]["headers"][0]["value"] == "value"

    config = AgentConfiguration(virtual=VirtualConfiguration(agent_id=RANDOM_AGENT_ID, configuration={"key": "value"}))

    dict_output = config.to_dict()
    assert "deployment" not in dict_output
    assert "virtual" in dict_output
    assert dict_output["virtual"]["agentId"] == RANDOM_AGENT_ID
    assert dict_output["virtual"]["configuration"] == {"key": "value"}


def test_agent_configuration_validation() -> None:
    with pytest.raises(ValueError) as e:
        AgentConfiguration(deployment=None, virtual=None)
    assert "Exactly one of deployment or virtual must be provided" in str(e.value)

    with pytest.raises(ValueError):
        AgentConfiguration(
            deployment=DeploymentConfiguration(url="http://example.com"),
            virtual=VirtualConfiguration(agent_id=RANDOM_AGENT_ID, configuration={}),
        )
    assert "Exactly one of deployment or virtual must be provided" in str(e.value)


def test_virtual_agent_configuration_validation() -> None:
    class TestConfig(BaseModel):
        text: str
        number: int

    class AnotherTestConfig(BaseModel):
        field: float

    config = VirtualConfiguration(agent_id=RANDOM_AGENT_ID, configuration={"text": "test", "number": 4})
    bad_config = VirtualConfiguration(agent_id=RANDOM_AGENT_ID, configuration={"text": "t", "number": "not a number"})

    config.validate_and_update(TestConfig)
    assert config == VirtualConfiguration(agent_id=RANDOM_AGENT_ID, configuration={"text": "test", "number": 4})

    with pytest.raises(ValidationError):
        config.validate_and_update(AnotherTestConfig)

    with pytest.raises(ValidationError):
        bad_config.validate_and_update(TestConfig)


def test_virtual_agent_configuration_update() -> None:
    class TestConfig(BaseModel):
        text: str
        number: int

        @field_validator("number", mode="after")
        @classmethod
        def validate_number(cls, v: int) -> int:
            return 42  # to illustrate reading from file, etc.

    config = VirtualConfiguration(agent_id=RANDOM_AGENT_ID, configuration={"text": "test", "number": 1})
    config.validate_and_update(TestConfig)
    assert config == VirtualConfiguration(agent_id=RANDOM_AGENT_ID, configuration={"text": "test", "number": 42})


def test_deployment_configuration_from_env() -> None:
    with OsEnviron("URL", "http://test_url"):
        data = {"url": {"fromEnv": "URL"}, "headers": []}
        deployment = DeploymentConfiguration.model_validate(data)

    assert deployment.url == "http://test_url"

    with pytest.raises(MissingEnvVariableException):
        data = {"url": {"fromEnv": "URL_NOT_SET"}, "headers": []}
        DeploymentConfiguration.model_validate(data)


def test_virtual_configuration_from_env() -> None:
    with OsEnviron("AGENT_ID", RANDOM_AGENT_ID):
        data = {"agent_id": {"fromEnv": "AGENT_ID"}, "configuration": {"key": "value"}}
        virtual = VirtualConfiguration.model_validate(data)

    assert virtual.agent_id == RANDOM_AGENT_ID

    with pytest.raises(MissingEnvVariableException):
        data = {"agent_id": {"fromEnv": "AGENT_ID_NOT_SET"}, "configuration": {"key": "value"}}
        VirtualConfiguration.model_validate(data)

    with OsEnviron("INVALID_AGENT_ID", "0xabc"), pytest.raises(TypeError):
        data = {"agent_id": {"fromEnv": "INVALID_AGENT_ID"}, "configuration": {"key": "value"}}
        VirtualConfiguration.model_validate(data)


def test_agent_data_owner() -> None:
    filename = os.path.join(DATA_DIR, "owner", "owner_agent.yaml")
    ad = AgentDataObject.from_yaml(filename)
    assert ad.spec.metadata.name == "Owner Agent"
    assert ad.spec.maybe_configuration is not None
    assert ad.spec.configuration.deployment is not None
    assert ad.spec.configuration.deployment.url == "http://192.168.2.36:8089"
    assert ad.metadata.has_label("env_prefix")
    assert ad.metadata.labels["env_prefix"] == "OWNER_"
    assert ad.metadata.labels["agent_type"] == "owner"


def test_agent_data_basic_a() -> None:
    filename = os.path.join(DATA_DIR, "basic", "basic_agent_a.yaml")
    ad = AgentDataObject.from_yaml(filename)
    assert ad.spec.metadata.name == "Basic Agent A"
    assert ad.spec.metadata.short_description == "Short description"
    assert ad.spec.metadata.long_description == "A much longer description"
    assert ad.spec.metadata.cost_card is None
    assert ad.metadata.has_label("env_prefix")
    assert ad.metadata.labels["env_prefix"] == "BASIC_A_"
    assert ad.metadata.labels["agent_type"] == "basic"


def test_agent_data_basic_b() -> None:
    filename = os.path.join(DATA_DIR, "basic", "basic_agent_b.yaml")
    ad = AgentDataObject.from_yaml(filename)
    assert ad.spec.metadata.name == "Basic Agent B"
    assert ad.spec.metadata.tags == ["tag3", "tag4"]
    assert ad.spec.metadata.example_prompts == ["Hello"]
    assert ad.spec.metadata.cost_card is not None
    assert ad.spec.metadata.cost_card == "Free"
    assert ad.metadata.has_label("env_prefix")
    assert ad.metadata.labels["env_prefix"] == "BASIC_B_"
    assert ad.metadata.labels["agent_type"] == "basic"


def test_agent_data_configurable() -> None:
    filename = os.path.join(DATA_DIR, "configurable", "configurable_agent.yaml")
    ad = AgentDataObject.from_yaml(filename)
    assert ad.spec.metadata.name == "Configurable Agent"
    assert ad.metadata.has_label("env_prefix")
    assert ad.metadata.labels["env_prefix"] == "CONFIGURABLE_"
    assert ad.metadata.labels["agent_type"] == "configurable"
