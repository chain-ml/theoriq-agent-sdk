import logging
import os
from typing import Dict, Final, Generator

import dotenv
import httpx
import pytest
from pydantic import BaseModel, Field
from tests.integration.utils import TEST_PARENT_AGENT_DATA, get_configurable_execute_output, join_threads, run_agent

from theoriq.api.v1alpha2 import AgentResponse
from theoriq.api.v1alpha2.manage import AgentManager
from theoriq.api.v1alpha2.message import Messenger
from theoriq.biscuit import TheoriqBudget
from theoriq.dialog import TextItemBlock
from theoriq.types import AgentConfiguration, AgentMetadata

dotenv.load_dotenv()

THEORIQ_API_KEY: Final[str] = os.environ["THEORIQ_API_KEY"]
user_manager = AgentManager.from_api_key(api_key=THEORIQ_API_KEY)

global_agent_map: Dict[str, AgentResponse] = {}


class TestConfig(BaseModel):
    text: str = Field(description="Text field")
    number: int = Field(description="An integer number")


def assert_send_message_to_configurable_agent(agent: AgentResponse, message: str = "Hello from user"):
    messenger = Messenger.from_api_key(api_key=THEORIQ_API_KEY)
    blocks = [TextItemBlock(message)]
    response = messenger.send_request(blocks=blocks, budget=TheoriqBudget.empty(), to_addr=agent.system.id)

    virtual = agent.configuration.ensure_virtual
    deployed_agent_name = global_agent_map[virtual.agent_id].metadata.name
    assert response.body.extract_last_text() == get_configurable_execute_output(
        virtual.configuration, message=message, agent_name=deployed_agent_name
    )


@pytest.fixture(scope="session", autouse=True)
def flask_apps() -> Generator[None, None, None]:
    logging.basicConfig(level=logging.INFO)
    thread = run_agent(agent_data_obj=TEST_PARENT_AGENT_DATA, schema=TestConfig.model_json_schema())
    yield
    join_threads([thread])


@pytest.mark.order(1)
def test_registration() -> None:
    agent = user_manager.create_agent(
        metadata=TEST_PARENT_AGENT_DATA.spec.metadata, configuration=TEST_PARENT_AGENT_DATA.spec.configuration
    )
    print(f"Successfully registered `{agent.metadata.name}` with id=`{agent.system.id}`\n")
    global_agent_map[agent.system.id] = agent


@pytest.mark.order(2)
def test_incorrect_configuration() -> None:
    parent_agent_id = list(global_agent_map.keys())[0]

    metadata = AgentMetadata(
        name="Incorrect Configurable Agent",
        short_description="Short description",
        long_description="Long description",
    )
    configuration = AgentConfiguration.for_virtual(agent_id=parent_agent_id, configuration={"incorrect": "config"})

    with pytest.raises(httpx.HTTPStatusError) as e:
        user_manager.create_agent(metadata=metadata, configuration=configuration)
    assert e.value.response.status_code == 502


@pytest.mark.order(3)
def test_configuration() -> None:
    parent_agent_id = list(global_agent_map.keys())[0]

    configs = [TestConfig(text="test value", number=42), TestConfig(text="another value", number=-5)]

    for i, config in enumerate(configs, start=1):
        metadata = AgentMetadata(
            name=f"Configurable Agent #{i}",
            short_description=f"Short description #{i}",
            long_description=f"Long description #{i}",
        )
        configuration = AgentConfiguration.for_virtual(agent_id=parent_agent_id, configuration=config.model_dump())

        agent = user_manager.create_agent(metadata=metadata, configuration=configuration)
        assert agent.configuration.is_virtual
        print(f"Successfully configured new `{agent.system.id}` with {config=}\n")
        global_agent_map[agent.system.id] = agent


@pytest.mark.order(4)
def test_messenger() -> None:
    for agent in global_agent_map.values():
        if agent.configuration.is_virtual:
            assert_send_message_to_configurable_agent(agent)
            continue

        with pytest.raises(httpx.HTTPStatusError) as e:
            assert_send_message_to_configurable_agent(agent)
        assert e.value.response.status_code == 400


@pytest.mark.order(5)
def test_update_configuration() -> None:
    agent = next(agent for agent_id, agent in global_agent_map.items() if agent.configuration.is_virtual)
    deployed_agent_id = agent.configuration.ensure_virtual.agent_id

    new_config = TestConfig(text="new test value", number=43)

    configuration = AgentConfiguration.for_virtual(agent_id=deployed_agent_id, configuration=new_config.model_dump())

    updated_agent = user_manager.update_agent(agent_id=agent.system.id, configuration=configuration)
    assert updated_agent.system.id == agent.system.id
    assert updated_agent.system.state == "configured"
    print(f"Successfully re-configured `{updated_agent.system.id}` with {new_config=}\n")
    global_agent_map[updated_agent.system.id] = updated_agent

    assert_send_message_to_configurable_agent(updated_agent)


@pytest.mark.order(-1)
def test_deletion() -> None:
    for agent in global_agent_map.values():
        user_manager.delete_agent(agent.system.id)
        print(f"Successfully deleted `{agent.system.id}`\n")
