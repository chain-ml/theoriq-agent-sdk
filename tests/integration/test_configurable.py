import logging
import os
from typing import Dict, Final, Generator

import dotenv
import httpx
import pytest
from pydantic import BaseModel, Field
from tests.integration.utils import (
    TEST_PARENT_AGENT_DATA,
    agent_data_obj_to_metadata,
    agent_data_obj_to_deployment_configuration,
    join_threads,
    run_configurable_agent,
)

from theoriq.api.v1alpha2 import AgentResponse
from theoriq.api.v1alpha2.configure import AgentConfigurator
from theoriq.api.v1alpha2.manage import AgentManager, Configuration, VirtualConfiguration, Metadata
from theoriq.api.v1alpha2.message import Messenger
from theoriq.biscuit import TheoriqBudget
from theoriq.dialog import TextItemBlock

dotenv.load_dotenv()

THEORIQ_API_KEY: Final[str] = os.environ["THEORIQ_API_KEY"]
user_manager = AgentManager.from_api_key(api_key=THEORIQ_API_KEY)

global_agent_map: Dict[str, AgentResponse] = {}


class TestConfig(BaseModel):
    field: str = Field(description="Text field")
    number: int = Field(description="An integer number")


@pytest.fixture(scope="session", autouse=True)
def flask_apps() -> Generator[None, None, None]:
    logging.basicConfig(level=logging.INFO)
    thread = run_configurable_agent(
        agent_data_obj=TEST_PARENT_AGENT_DATA,
        schema=TestConfig.model_json_schema(),
        agent_configurator=AgentConfigurator.default(),
    )
    yield
    join_threads([thread])


@pytest.mark.order(1)
def test_registration() -> None:
    metadata = agent_data_obj_to_metadata(TEST_PARENT_AGENT_DATA)
    configuration = agent_data_obj_to_deployment_configuration(TEST_PARENT_AGENT_DATA)
    agent = user_manager.create_agent(metadata=metadata, configuration=configuration)
    print(f"Successfully registered `{agent.metadata.name}` with id=`{agent.system.id}`\n")
    global_agent_map[agent.system.id] = agent


@pytest.mark.order(2)
def test_configuration() -> None:
    for agent_id in global_agent_map.keys():
        metadata = Metadata(
            name="Name",
            shortDescription="agent.spec.metadata.descriptions.short",
            longDescription="agent.spec.metadata.descriptions.long",
            tags=[],
            examplePrompts=[],
        )

        agent = user_manager.configure_agent(agent_id, metadata=metadata, config={"test": "abc"})
        # assert agent.system.state == "online"
        print(f"Successfully configured `{agent_id}`\n")


@pytest.mark.order(5)
def test_messenger() -> None:
    message = "Hello from user"
    blocks = [TextItemBlock(message)]
    messenger = Messenger.from_api_key(api_key=THEORIQ_API_KEY)

    for agent_id, agent in global_agent_map.items():
        # if not agent.is_configurable:
        #     response = messenger.send_request(blocks=blocks, budget=TheoriqBudget.empty(), to_addr=agent_id)
        #     assert response.body.extract_last_text() == get_echo_execute_output(
        #         message=message, agent_name=agent.metadata.name
        #     )
        #     continue

        with pytest.raises(httpx.HTTPStatusError) as e:
            messenger.send_request(blocks=blocks, budget=TheoriqBudget.empty(), to_addr=agent_id)
        assert e.value.response.status_code == 400


@pytest.mark.order(-1)
def test_deletion() -> None:
    for agent in global_agent_map.values():
        user_manager.delete_agent(agent.system.id)
        print(f"Successfully deleted `{agent.system.id}`\n")
