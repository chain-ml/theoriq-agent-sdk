import os.path

from tests import DATA_DIR

from theoriq.types import AgentDataObject


def test_agent_data_parent() -> None:
    filename = os.path.join(DATA_DIR, "parent_agent.yaml")
    ad = AgentDataObject.from_yaml(filename)
    assert ad.spec.metadata.name == "Parent Agent"
    assert ad.spec.configuration is not None
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
