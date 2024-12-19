import os.path

from theoriq.types import AgentDataObject


def test_agent_data():
    filename = os.path.join(os.path.dirname(__file__), "../data/agent.yaml")
    ad = AgentDataObject.from_yaml(filename)
    assert ad.spec.urls.end_point == "http://127.0.0.1:8000/"
    assert ad.metadata.name == "AwesomeSum"
