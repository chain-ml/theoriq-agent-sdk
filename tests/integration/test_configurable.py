import logging
import os
from typing import Dict, Final, Generator

import dotenv
import httpx
import pytest
from pydantic import BaseModel, Field
from tests.integration.utils import TEST_PARENT_AGENT_DATA, get_configurable_execute_output, join_threads, run_agent
from tests.integration.conftest import get_agent_map

from theoriq.api.v1alpha2 import AgentResponse
from theoriq.api.v1alpha2.manage import AgentConfigurationError, DeployedAgentManager, VirtualAgentManager
from theoriq.api.v1alpha2.message import Messenger
from theoriq.biscuit import TheoriqBudget
from theoriq.dialog import TextItemBlock
from theoriq.types import AgentConfiguration, AgentMetadata

dotenv.load_dotenv()

THEORIQ_API_KEY: Final[str] = os.environ["THEORIQ_API_KEY"]
user_manager = DeployedAgentManager.from_api_key(api_key=THEORIQ_API_KEY)
user_manager_configurable = VirtualAgentManager.from_api_key(api_key=THEORIQ_API_KEY)


class TestConfig(BaseModel):
    text: str = Field(description="Text field")
    number: int = Field(description="An integer number")


def assert_send_message_to_configurable_agent(agent: AgentResponse, message: str = "Hello from user"):
    messenger = Messenger.from_api_key(api_key=THEORIQ_API_KEY)
    blocks = [TextItemBlock(message)]
    response = messenger.send_request(blocks=blocks, budget=TheoriqBudget.empty(), to_addr=agent.system.id)

    virtual = agent.configuration.ensure_virtual
    global_agent_map = get_agent_map("test_configurable")
    deployed_agent_name = global_agent_map[virtual.agent_id].metadata.name
    assert response.body.extract_last_text() == get_configurable_execute_output(
        virtual.configuration, message=message, agent_name=deployed_agent_name
    )


# Use shared fixtures instead of local ones
@pytest.mark.usefixtures("shared_flask_apps")
@pytest.mark.order(1)
def test_registration() -> None:
    global_agent_map = get_agent_map("test_configurable")
    agent = user_manager.create_agent(
        metadata=TEST_PARENT_AGENT_DATA.spec.metadata, configuration=TEST_PARENT_AGENT_DATA.spec.configuration
    )
    print(f"Successfully registered `{agent.metadata.name}` with id=`{agent.system.id}`\n")
    global_agent_map[agent.system.id] = agent


@pytest.mark.usefixtures("shared_flask_apps")
@pytest.mark.order(2)
def test_incorrect_configuration() -> None:
    global_agent_map = get_agent_map("test_configurable")
    deployed_agent = next(agent for agent_id, agent in global_agent_map.items() if agent.configuration.is_deployed)

    metadata = AgentMetadata(
        name="Incorrect Configurable Agent",
        short_description="Short description",
        long_description="Long description",
        tags=["test_to_delete"],
    )
    configuration = AgentConfiguration.for_virtual(
        agent_id=deployed_agent.system.id, configuration={"incorrect": "config"}
    )

    with pytest.raises(AgentConfigurationError) as e:
        user_manager_configurable.create_agent(metadata=metadata, configuration=configuration)
    assert e.value.message.endswith("created but failed to configure")
    assert isinstance(e.value.original_exception, httpx.HTTPStatusError)
    assert e.value.original_exception.response.status_code == 502

    user_manager_configurable.delete_agent(e.value.agent.system.id)


@pytest.mark.usefixtures("shared_flask_apps")
@pytest.mark.order(3)
def test_configuration() -> None:
    global_agent_map = get_agent_map("test_configurable")
    parent_agent_id = list(global_agent_map.keys())[0]

    configs = [TestConfig(text="test value", number=42), TestConfig(text="another value", number=-5)]

    for i, config in enumerate(configs, start=1):
        metadata = AgentMetadata(
            name=f"Configurable Agent #{i}",
            short_description=f"Short description #{i}",
            long_description=f"Long description #{i}",
        )
        configuration = AgentConfiguration.for_virtual(agent_id=parent_agent_id, configuration=config.model_dump())

        agent = user_manager_configurable.create_agent(metadata=metadata, configuration=configuration)
        assert agent.configuration.is_virtual
        print(f"Successfully configured new `{agent.system.id}` with {config=}\n")
        global_agent_map[agent.system.id] = agent


@pytest.mark.usefixtures("shared_flask_apps")
@pytest.mark.order(4)
def test_mint_agent() -> None:
    global_agent_map = get_agent_map("test_configurable")
    for agent_id in global_agent_map.keys():
        agent = user_manager_configurable.mint_agent(agent_id)
        assert agent.system.state == "online"
        print(f"Successfully minted `{agent_id}`\n")


@pytest.mark.usefixtures("shared_flask_apps")
@pytest.mark.order(5)
def test_unmint_agent() -> None:
    # TODO: investigate agents break after unmint - abc is not executable by xyz
    global_agent_map = get_agent_map("test_configurable")
    for agent_id in global_agent_map.keys():
        agent = user_manager_configurable.unmint_agent(agent_id)
        assert agent.system.state == "configured"
        print(f"Successfully unminted `{agent_id}`\n")


@pytest.mark.usefixtures("shared_flask_apps")
@pytest.mark.order(6)
def test_messenger() -> None:
    global_agent_map = get_agent_map("test_configurable")
    for agent in global_agent_map.values():
        if agent.configuration.is_virtual:
            assert_send_message_to_configurable_agent(agent)
            continue

        with pytest.raises(httpx.HTTPStatusError) as e:
            assert_send_message_to_configurable_agent(agent)
        assert e.value.response.status_code == 400


@pytest.mark.usefixtures("shared_flask_apps")
@pytest.mark.order(7)
def test_incorrect_update_configuration() -> None:
    global_agent_map = get_agent_map("test_configurable")
    agent = next(agent for agent_id, agent in global_agent_map.items() if agent.configuration.is_virtual)
    deployed_agent_id = agent.configuration.ensure_virtual.agent_id

    metadata = AgentMetadata(
        name="Incorrectly Updated Configurable Agent",
        short_description="Short description",
        long_description="Long description",
        tags=["test_to_delete"],
    )
    configuration = AgentConfiguration.for_virtual(agent_id=deployed_agent_id, configuration={"incorrect": "config"})

    with pytest.raises(AgentConfigurationError) as e:
        user_manager_configurable.update_agent(agent_id=agent.system.id, metadata=metadata, configuration=configuration)
    assert e.value.message.endswith("updated but failed to configure")
    assert isinstance(e.value.original_exception, httpx.HTTPStatusError)
    assert e.value.original_exception.response.status_code == 502


@pytest.mark.usefixtures("shared_flask_apps")
@pytest.mark.order(8)
def test_update_configuration() -> None:
    global_agent_map = get_agent_map("test_configurable")
    agent = next(agent for agent_id, agent in global_agent_map.items() if agent.configuration.is_virtual)
    deployed_agent_id = agent.configuration.ensure_virtual.agent_id

    new_config = TestConfig(text="new test value", number=43)

    configuration = AgentConfiguration.for_virtual(agent_id=deployed_agent_id, configuration=new_config.model_dump())

    updated_agent = user_manager_configurable.update_agent(agent_id=agent.system.id, configuration=configuration)
    assert updated_agent.system.id == agent.system.id
    assert updated_agent.system.state == "configured"
    print(f"Successfully re-configured `{updated_agent.system.id}` with {new_config=}\n")
    global_agent_map[updated_agent.system.id] = updated_agent

    assert_send_message_to_configurable_agent(updated_agent)


@pytest.mark.usefixtures("shared_flask_apps")
@pytest.mark.order(-1)
def test_deletion() -> None:
    global_agent_map = get_agent_map("test_configurable")
    for agent in global_agent_map.values():
        user_manager_configurable.delete_agent(agent.system.id)
        print(f"Successfully deleted `{agent.system.id}`\n")
