import datetime
import logging
import os
from typing import Dict, Final, Generator

import dotenv
import httpx
import pytest
from pydantic import BaseModel, Field
from tests.integration.utils import (
    TEST_PARENT_AGENT_DATA,
    get_configurable_execute_output,
    join_threads,
    run_configurable_agent,
)

from theoriq.api.v1alpha2 import AgentResponse
from theoriq.api.v1alpha2.configure import AgentConfigurator
from theoriq.api.v1alpha2.manage import AgentManager
from theoriq.api.v1alpha2.message import Messenger
from theoriq.biscuit import TheoriqBudget
from theoriq.dialog import TextItemBlock
from theoriq.types import AgentMetadata

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
    agent = user_manager.create_agent(
        metadata=TEST_PARENT_AGENT_DATA.spec.metadata, configuration=TEST_PARENT_AGENT_DATA.spec.configuration
    )
    print(f"Successfully registered `{agent.metadata.name}` with id=`{agent.system.id}`\n")
    global_agent_map[agent.system.id] = agent


@pytest.mark.order(2)
def test_configuration() -> None:
    parent_agent_id = list(global_agent_map.keys())[0]

    metadata = AgentMetadata(
        name=f"Configurable {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        short_description="short",
        long_description="long",
    )

    config = {"field": "test", "number": 5}

    agent = user_manager.configure_agent(agent_id=parent_agent_id, metadata=metadata, config=config)
    assert agent.system.state == "configured"
    print(f"Successfully configured new `{agent.system.id}` with {config=}\n")
    global_agent_map[agent.system.id] = agent


@pytest.mark.order(5)
def test_messenger() -> None:
    message = "Hello from user"
    blocks = [TextItemBlock(message)]
    messenger = Messenger.from_api_key(api_key=THEORIQ_API_KEY)

    for agent_id, agent in global_agent_map.items():
        if agent.system.state == "configured" and "requireConfiguration" not in agent.system.tags:
            response = messenger.send_request(blocks=blocks, budget=TheoriqBudget.empty(), to_addr=agent_id)
            if agent.configuration.virtual is None:
                raise RuntimeError
            assert response.body.extract_last_text() == get_configurable_execute_output(
                agent.configuration.virtual.configuration
            )
            continue

        with pytest.raises(httpx.HTTPStatusError) as e:
            messenger.send_request(blocks=blocks, budget=TheoriqBudget.empty(), to_addr=agent_id)
        assert e.value.response.status_code == 400


@pytest.mark.order(-1)
def test_deletion() -> None:
    for agent in global_agent_map.values():
        user_manager.delete_agent(agent.system.id)
        print(f"Successfully deleted `{agent.system.id}`\n")
