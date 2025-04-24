import os.path

from tests import DATA_DIR

from theoriq.types import AgentDataObject


def test_agent_data():
    filename = os.path.join(DATA_DIR, "agent_a.yaml")
    ad = AgentDataObject.from_yaml(filename)
    assert ad.spec.urls.end_point == "http://192.168.2.36:8090"
    assert ad.metadata.name == "Agent A"
