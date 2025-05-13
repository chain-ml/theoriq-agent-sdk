import logging
import os
import time
from typing import Dict, Final, Generator, List

import dotenv
import pytest
from tests.integration.utils import (
    PARENT_AGENT_ENV_PREFIX,
    PARENT_AGENT_NAME,
    TEST_AGENT_DATA_LIST,
    TEST_CHILD_AGENT_DATA_LIST,
    agent_data_obj_to_deployment_configuration,
    agent_data_obj_to_metadata,
    join_threads,
    run_echo_agents,
)

from theoriq.api.v1alpha2 import AgentResponse
from theoriq.api.v1alpha2.manage import AgentManager
from theoriq.api.v1alpha2.publish import Publisher, PublisherContext
from theoriq.api.v1alpha2.subscribe import Subscriber
from theoriq.biscuit import AgentAddress

dotenv.load_dotenv()

THEORIQ_API_KEY: Final[str] = os.environ["THEORIQ_API_KEY"]
user_manager = AgentManager.from_api_key(api_key=THEORIQ_API_KEY)

global_agent_map: Dict[str, AgentResponse] = {}
global_notification_queue_pub: List[str] = []


def publishing_job(context: PublisherContext) -> None:
    i = 0
    while True:
        notification = f"Sample notification #{i}"
        global_notification_queue_pub.append(notification)
        context.publish(notification)

        i += 1
        time.sleep(0.3)


def assert_notification_queues(notification_queue_sub: List[str]) -> None:
    # every element in subscriber queue must be in global_notification_queue_pub
    # not the other way around because publisher starts publishing before subscriber subscribes

    assert len(notification_queue_sub) <= len(global_notification_queue_pub)

    for notification in notification_queue_sub:
        assert notification in global_notification_queue_pub


def get_parent_agent_address() -> AgentAddress:
    maybe_parent_agent = next(
        (agent for agent in global_agent_map.values() if agent.metadata.name == PARENT_AGENT_NAME), None
    )
    if maybe_parent_agent is None:
        raise RuntimeError("Parent agent data object not found")
    return AgentAddress(maybe_parent_agent.system.id)


@pytest.fixture(scope="session", autouse=True)
def flask_apps() -> Generator[None, None, None]:
    logging.basicConfig(level=logging.INFO)
    threads = run_echo_agents(TEST_AGENT_DATA_LIST)
    yield
    join_threads(threads)


@pytest.mark.order(1)
def test_registration() -> None:
    for agent_data_obj in TEST_AGENT_DATA_LIST:
        metadata = agent_data_obj_to_metadata(agent_data_obj)
        configuration = agent_data_obj_to_deployment_configuration(agent_data_obj)
        agent = user_manager.create_agent(metadata=metadata, configuration=configuration)
        print(f"Successfully registered `{agent.metadata.name}` with id=`{agent.system.id}`\n")
        global_agent_map[agent.system.id] = agent


@pytest.mark.order(2)
def test_publishing() -> None:
    """Parent agent is a publisher."""

    publisher = Publisher.from_env(env_prefix=PARENT_AGENT_ENV_PREFIX)
    publisher.new_job(job=publishing_job, background=True).start()


@pytest.mark.order(3)
def test_subscribing_as_agent() -> None:
    """Child agent is a subscriber."""

    agent_notification_queue_sub: List[str] = []

    def subscribing_handler(notification: str) -> None:
        agent_notification_queue_sub.append(notification)

    child_agent_data = TEST_CHILD_AGENT_DATA_LIST[0]
    subscriber = Subscriber.from_env(env_prefix=child_agent_data.metadata.labels["env_prefix"])
    subscriber.new_job(agent_address=get_parent_agent_address(), handler=subscribing_handler, background=True).start()

    time.sleep(1.0)
    assert_notification_queues(agent_notification_queue_sub)


@pytest.mark.order(4)
def test_subscribing_as_user() -> None:
    """User is a subscriber."""

    user_notification_queue_sub: List[str] = []

    def subscribing_handler(notification: str) -> None:
        user_notification_queue_sub.append(notification)

    subscriber = Subscriber.from_api_key(api_key=THEORIQ_API_KEY)
    subscriber.new_job(agent_address=get_parent_agent_address(), handler=subscribing_handler, background=True).start()

    time.sleep(1.0)
    assert_notification_queues(user_notification_queue_sub)


@pytest.mark.order(-1)
def test_deletion() -> None:
    for agent in global_agent_map.values():
        user_manager.delete_agent(agent.system.id)
        print(f"Successfully deleted `{agent.system.id}`\n")
