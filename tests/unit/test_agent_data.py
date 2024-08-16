from theoriq.types import AgentDataObject


def test_agent_data():
    ad = AgentDataObject.from_yaml("../data/agent.yaml")
    assert ad.spec.urls.end_point == "http://127.0.0.1:8000/"
    assert ad.metadata.name == "AwesumSum"
