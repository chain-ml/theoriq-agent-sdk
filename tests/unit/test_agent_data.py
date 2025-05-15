import os.path

import pytest
from tests import DATA_DIR

from theoriq.types import (
    AgentConfiguration,
    AgentDataObject,
    AgentMetadata,
    DeploymentConfiguration,
    Header,
    VirtualConfiguration,
)


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

    config = AgentConfiguration(virtual=VirtualConfiguration(agent_id="0xabc", configuration={"key": "value"}))

    dict_output = config.to_dict()
    assert "deployment" not in dict_output
    assert "virtual" in dict_output
    assert dict_output["virtual"]["agentId"] == "0xabc"
    assert dict_output["virtual"]["configuration"] == {"key": "value"}


def test_agent_configuration_validation() -> None:
    with pytest.raises(ValueError) as e:
        AgentConfiguration(deployment=None, virtual=None)
    assert "Exactly one of deployment or virtual must be provided" in str(e.value)

    with pytest.raises(ValueError):
        AgentConfiguration(
            deployment=DeploymentConfiguration(url="http://example.com"),
            virtual=VirtualConfiguration(agent_id="0xabc", configuration={}),
        )
    assert "Exactly one of deployment or virtual must be provided" in str(e.value)


def test_agent_data_parent() -> None:
    filename = os.path.join(DATA_DIR, "parent_agent.yaml")
    ad = AgentDataObject.from_yaml(filename)
    assert ad.spec.metadata.name == "Parent Agent"
    assert ad.spec.maybe_configuration is not None
    assert ad.spec.configuration.deployment is not None
    assert ad.spec.configuration.deployment.url == "http://192.168.2.36:8089"
    assert ad.metadata.has_label("env_prefix")
    assert ad.metadata.labels["env_prefix"] == "PARENT_"


def test_agent_data_child_a() -> None:
    filename = os.path.join(DATA_DIR, "child_agent_a.yaml")
    ad = AgentDataObject.from_yaml(filename)
    assert ad.spec.metadata.name == "Child Agent A"
    assert ad.spec.metadata.short_description == "Short description"
    assert ad.spec.metadata.long_description == "A much longer description"
    assert ad.spec.metadata.cost_card is None
    assert ad.metadata.has_label("env_prefix")
    assert ad.metadata.labels["env_prefix"] == "CHILD_A_"


def test_agent_data_child_b() -> None:
    filename = os.path.join(DATA_DIR, "child_agent_b.yaml")
    ad = AgentDataObject.from_yaml(filename)
    assert ad.spec.metadata.name == "Child Agent B"
    assert ad.spec.metadata.tags == ["tag3", "tag4"]
    assert ad.spec.metadata.example_prompts == ["Hello"]
    assert ad.spec.metadata.cost_card is not None
    assert ad.spec.metadata.cost_card == "Free"
    assert ad.metadata.has_label("env_prefix")
    assert ad.metadata.labels["env_prefix"] == "CHILD_B_"
