from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Dict

import pytest
from tests.integration.agent_registry import AgentRegistry, AgentType
from tests.integration.agent_runner import AgentRunner
from tests.integration.utils import agents_are_equal

from theoriq import AgentDeploymentConfiguration
from theoriq.api.v1alpha2 import AgentResponse
from theoriq.api.v1alpha2.manage import AgentManager
from theoriq.api.v1alpha2.message import Messenger


@pytest.mark.order(1)
@pytest.mark.usefixtures("agent_flask_apps")
def test_registration(
    agent_registry: AgentRegistry, agent_map: Dict[str, AgentResponse], user_manager: AgentManager
) -> None:
    agent_data_objs = agent_registry.get_agents_of_types([AgentType.OWNER, AgentType.BASIC])
    for agent_data in agent_data_objs:
        agent = user_manager.create_agent_from_data(agent_data)
        agent_map[agent.system.id] = agent


@pytest.mark.order(2)
@pytest.mark.usefixtures("agent_flask_apps")
def test_minting(agent_map: Dict[str, AgentResponse], user_manager: AgentManager) -> None:
    for agent_id in agent_map.keys():
        agent = user_manager.mint_agent(agent_id)
        assert agent.system.state == "online"


@pytest.mark.order(3)
@pytest.mark.usefixtures("agent_flask_apps")
def test_get_agents(agent_map: Dict[str, AgentResponse], user_manager: AgentManager) -> None:
    agents = user_manager.get_agents()
    assert len(agents) >= len(agent_map.keys())
    fetched_agents: Dict[str, AgentResponse] = {agent.system.id: agent for agent in agents}

    for agent in agent_map.values():
        assert agent.system.id in fetched_agents
        assert agents_are_equal(agent, fetched_agents[agent.system.id])

        same_agent = user_manager.get_agent(agent.system.id)
        assert agents_are_equal(agent, same_agent)

        assert agent.schemas.execute is not None
        assert agent.schemas.notification is not None


@pytest.mark.order(4)
@pytest.mark.usefixtures("agent_flask_apps")
def test_unminting(agent_map: Dict[str, AgentResponse], user_manager: AgentManager) -> None:
    for agent_id in agent_map.keys():
        agent = user_manager.unmint_agent(agent_id)
        assert agent.system.state == "configured"


@pytest.mark.order(5)
@pytest.mark.usefixtures("agent_flask_apps")
def test_messenger(agent_map: Dict[str, AgentResponse], user_messenger: Messenger) -> None:
    message = "Hello from user"

    for agent_id, agent in agent_map.items():
        response = user_messenger.send_text_request(message=message, to_addr=agent_id)
        actual = response.body.extract_last_text()
        expected = AgentRunner.get_echo_execute_output(message=message, agent_name=agent.metadata.name)
        assert actual == expected


@pytest.mark.order(6)
@pytest.mark.usefixtures("agent_flask_apps")
def test_updating(agent_registry: AgentRegistry, user_manager: AgentManager) -> None:
    owner_agent_data = agent_registry.get_first_agent_of_type(AgentType.OWNER)
    updated_agent_data = deepcopy(owner_agent_data)
    updated_agent_data.spec.metadata.name = "Updated Owner Agent"

    config = AgentDeploymentConfiguration.from_env(env_prefix=owner_agent_data.metadata.labels["env_prefix"])

    response = user_manager.update_agent(agent_id=str(config.address), metadata=updated_agent_data.spec.metadata)

    assert response.metadata.name == "Updated Owner Agent"


@pytest.mark.order(7)
@pytest.mark.usefixtures("agent_flask_apps")
def test_system_tag(agent_registry: AgentRegistry, user_manager: AgentManager) -> None:
    owner_agent_data = agent_registry.get_first_agent_of_type(AgentType.OWNER)
    config = AgentDeploymentConfiguration.from_env(env_prefix=owner_agent_data.metadata.labels["env_prefix"])

    user_manager.add_system_tag(agent_id=str(config.address), tag="curated")

    agent = user_manager.get_agent(agent_id=str(config.address))
    assert "curated" in agent.system.tags

    user_manager.delete_system_tag(agent_id=str(config.address), tag="curated")

    agent = user_manager.get_agent(agent_id=str(config.address))
    assert "curated" not in agent.system.tags


@pytest.mark.order(8)
@pytest.mark.usefixtures("agent_flask_apps")
def test_create_api_key(user_manager: AgentManager) -> None:
    expires_at = datetime.now(tz=timezone.utc) + timedelta(minutes=1)
    response = user_manager.create_api_key(expires_at)

    assert isinstance(response["biscuit"], str)
    assert response["data"]["expiresAt"] == int(expires_at.timestamp())


@pytest.mark.order(-1)
@pytest.mark.usefixtures("agent_flask_apps")
def test_deletion(agent_map: Dict[str, AgentResponse], user_manager: AgentManager) -> None:
    for agent in agent_map.values():
        user_manager.delete_agent(agent.system.id)
