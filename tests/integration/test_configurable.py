import os
from typing import Dict

import httpx
import pytest
from tests.integration.agent_registry import AgentRegistry, AgentType
from tests.integration.agent_runner import AgentRunner, TestConfig

from theoriq.api.v1alpha2 import AgentResponse
from theoriq.api.v1alpha2.manage import AgentConfigurationError, DeployedAgentManager, VirtualAgentManager
from theoriq.api.v1alpha2.message import Messenger
from theoriq.biscuit import TheoriqBudget
from theoriq.dialog import TextItemBlock
from theoriq.types import AgentConfiguration, AgentMetadata


@pytest.fixture()
def virtual_manager() -> VirtualAgentManager:
    return VirtualAgentManager.from_api_key(api_key=os.environ["THEORIQ_API_KEY"])


def assert_send_message_to_configurable_agent(
    agent: AgentResponse, agent_map: Dict[str, AgentResponse], messenger: Messenger, message: str = "Hello from user"
) -> None:
    blocks = [TextItemBlock(message)]
    response = messenger.send_request(blocks=blocks, budget=TheoriqBudget.empty(), to_addr=agent.system.id)

    virtual = agent.configuration.ensure_virtual
    deployed_agent_name = agent_map[virtual.agent_id].metadata.name
    actual = response.body.extract_last_text()
    expected = AgentRunner.get_configurable_execute_output(
        virtual.configuration, message=message, agent_name=deployed_agent_name
    )
    assert actual == expected


@pytest.mark.order(1)
@pytest.mark.usefixtures("agent_flask_apps")
def test_registration(
    agent_registry: AgentRegistry, agent_map: Dict[str, AgentResponse], user_manager: DeployedAgentManager
) -> None:
    configurable_agent_data = agent_registry.get_first_agent_of_type(AgentType.CONFIGURABLE)
    agent = user_manager.create_agent(configurable_agent_data.spec.metadata, configurable_agent_data.spec.configuration)

    assert agent.schemas.configuration is not None
    agent_map[agent.system.id] = agent


@pytest.mark.order(2)
@pytest.mark.usefixtures("agent_flask_apps")
def test_incorrect_configuration(agent_map: Dict[str, AgentResponse], virtual_manager: VirtualAgentManager) -> None:
    deployed_agent = next(agent for agent in agent_map.values() if agent.configuration.is_deployed)

    metadata = AgentMetadata(
        name="Incorrect Configurable Agent",
        short_description="Short description",
        long_description="Long description",
    )
    configuration = AgentConfiguration.for_virtual(
        agent_id=deployed_agent.system.id, configuration={"incorrect": "config"}
    )

    with pytest.raises(AgentConfigurationError) as e:
        virtual_manager.create_agent(metadata, configuration)
    assert e.value.message.endswith("created but failed to configure")
    assert isinstance(e.value.original_exception, httpx.HTTPStatusError)
    assert e.value.original_exception.response.status_code == 502

    virtual_manager.delete_agent(e.value.agent.system.id)


@pytest.mark.order(3)
@pytest.mark.usefixtures("agent_flask_apps")
def test_configuration(agent_map: Dict[str, AgentResponse], virtual_manager: VirtualAgentManager) -> None:
    deployed_agent = next(agent for agent in agent_map.values() if agent.configuration.is_deployed)

    configs = [TestConfig(text="test value", number=42), TestConfig(text="another value", number=-5)]

    for i, config in enumerate(configs, start=1):
        metadata = AgentMetadata(
            name=f"Configurable Agent #{i}",
            short_description=f"Short description #{i}",
            long_description=f"Long description #{i}",
        )
        configuration = AgentConfiguration.for_virtual(
            agent_id=deployed_agent.system.id, configuration=config.model_dump()
        )

        agent = virtual_manager.create_agent(metadata, configuration)
        assert agent.configuration.is_virtual
        agent_map[agent.system.id] = agent


@pytest.mark.order(4)
@pytest.mark.usefixtures("agent_flask_apps")
def test_messenger(agent_map: Dict[str, AgentResponse], user_messenger: Messenger) -> None:
    for agent in agent_map.values():
        if agent.configuration.is_virtual:
            assert_send_message_to_configurable_agent(agent, agent_map, user_messenger)
            continue

        with pytest.raises(httpx.HTTPStatusError) as e:
            assert_send_message_to_configurable_agent(agent, agent_map, user_messenger)
        assert e.value.response.status_code == 400


@pytest.mark.order(5)
@pytest.mark.usefixtures("agent_flask_apps")
def test_incorrect_update_configuration(
    agent_map: Dict[str, AgentResponse], virtual_manager: VirtualAgentManager
) -> None:
    virtual_agent = next(agent for agent in agent_map.values() if agent.configuration.is_virtual)
    deployed_agent_id = virtual_agent.configuration.ensure_virtual.agent_id

    metadata = AgentMetadata(
        name="Incorrectly Updated Configurable Agent",
        short_description="Short description",
        long_description="Long description",
    )
    configuration = AgentConfiguration.for_virtual(agent_id=deployed_agent_id, configuration={"incorrect": "config"})

    with pytest.raises(AgentConfigurationError) as e:
        virtual_manager.update_agent(agent_id=virtual_agent.system.id, metadata=metadata, configuration=configuration)
    assert e.value.message.endswith("updated but failed to configure")
    assert isinstance(e.value.original_exception, httpx.HTTPStatusError)
    assert e.value.original_exception.response.status_code == 502


@pytest.mark.order(8)
@pytest.mark.usefixtures("agent_flask_apps")
def test_update_configuration(
    agent_map: Dict[str, AgentResponse], virtual_manager: VirtualAgentManager, user_messenger: Messenger
) -> None:
    virtual_agent = next(agent for agent in agent_map.values() if agent.configuration.is_virtual)
    deployed_agent_id = virtual_agent.configuration.ensure_virtual.agent_id

    new_config = TestConfig(text="new test value", number=43)

    configuration = AgentConfiguration.for_virtual(agent_id=deployed_agent_id, configuration=new_config.model_dump())

    updated_agent = virtual_manager.update_agent(agent_id=virtual_agent.system.id, configuration=configuration)
    assert updated_agent.system.id == virtual_agent.system.id
    assert updated_agent.system.state == "configured"
    agent_map[updated_agent.system.id] = updated_agent

    assert_send_message_to_configurable_agent(updated_agent, agent_map, user_messenger)


@pytest.mark.order(-1)
@pytest.mark.usefixtures("agent_flask_apps")
def test_deletion(agent_map: Dict[str, AgentResponse], virtual_manager: VirtualAgentManager) -> None:
    for agent in agent_map.values():
        virtual_manager.delete_agent(agent.system.id)
        print(f"Successfully deleted `{agent.system.id}`\n")
