import os.path

from tests import DATA_DIR

from theoriq.types import AgentDataObject


def test_agent_data_parent() -> None:
    filename = os.path.join(DATA_DIR, "parent_agent.yaml")
    ad = AgentDataObject.from_yaml(filename)
    assert ad.metadata.name == "Parent Agent"
    assert ad.spec.urls.end_point == "http://192.168.2.36:8089"
    assert ad.metadata.labels["env_prefix"] == "PARENT_"


def test_agent_data_child_a() -> None:
    filename = os.path.join(DATA_DIR, "child_agent_a.yaml")
    ad = AgentDataObject.from_yaml(filename)
    assert ad.metadata.name == "Child Agent A"
    assert ad.spec.metadata.descriptions.short == "Short description"
    assert ad.spec.metadata.descriptions.long == "A much longer description"
    assert ad.metadata.labels["env_prefix"] == "CHILD_A_"


def test_agent_data_child_b() -> None:
    filename = os.path.join(DATA_DIR, "child_agent_b.yaml")
    ad = AgentDataObject.from_yaml(filename)
    assert ad.metadata.name == "Child Agent B"
    assert ad.spec.metadata.tags == ["tag3", "tag4"]
    assert ad.spec.metadata.examples == ["Hello"]
    assert ad.metadata.labels["env_prefix"] == "CHILD_B_"
