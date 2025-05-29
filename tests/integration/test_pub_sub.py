import os
import time
from typing import Dict, Generator, List

import pytest
from tests.integration.agent_registry import AgentRegistry, AgentType

from theoriq.api.v1alpha2 import AgentResponse
from theoriq.api.v1alpha2.manage import DeployedAgentManager
from theoriq.api.v1alpha2.publish import Publisher, PublisherContext
from theoriq.api.v1alpha2.subscribe import Subscriber
from theoriq.biscuit import AgentAddress


@pytest.fixture(scope="module")
def notification_queue() -> Generator[List[str], None, None]:
    notification_queue: List[str] = []
    yield notification_queue
    notification_queue.clear()


def assert_notification_queues(*, publisher_queue: List[str], subscriber_queue: List[str]) -> None:
    # every element in subscriber queue must be in publisher queue
    # not the other way around because publisher starts publishing before subscriber subscribes

    assert 0 < len(subscriber_queue) <= len(publisher_queue)

    for notification in subscriber_queue:
        assert notification in publisher_queue


def get_owner_agent_address(agent_registry: AgentRegistry, agent_map: Dict[str, AgentResponse]) -> AgentAddress:
    owner_agent_data = agent_registry.get_first_agent_of_type(AgentType.OWNER)
    owner_name = owner_agent_data.spec.metadata.name
    owner_agent = next(agent for agent in agent_map.values() if agent.metadata.name == owner_name)
    return AgentAddress(owner_agent.system.id)


@pytest.mark.order(1)
@pytest.mark.usefixtures("agent_flask_apps")
def test_registration(
    agent_registry: AgentRegistry, agent_map: Dict[str, AgentResponse], user_manager: DeployedAgentManager
) -> None:
    agent_data_objs = agent_registry.get_agents_of_types([AgentType.OWNER, AgentType.BASIC])
    for agent_data in agent_data_objs:
        agent = user_manager.create_agent(agent_data.spec.metadata, agent_data.spec.configuration)
        agent_map[agent.system.id] = agent


@pytest.mark.order(2)
@pytest.mark.usefixtures("agent_flask_apps")
def test_publishing(agent_registry: AgentRegistry, notification_queue: List[str]) -> None:
    def publishing_job(context: PublisherContext) -> None:
        i = 0
        while True:
            notification = f"Sample notification #{i}"
            notification_queue.append(notification)
            context.publish(notification)

            i += 1
            time.sleep(0.3)

    owner_agent_data = agent_registry.get_first_agent_of_type(AgentType.OWNER)
    publisher = Publisher.from_env(env_prefix=owner_agent_data.metadata.labels["env_prefix"])
    publisher.new_job(job=publishing_job, background=True).start()


@pytest.mark.order(3)
@pytest.mark.usefixtures("agent_flask_apps")
def test_subscribing_as_agent(
    agent_registry: AgentRegistry, agent_map: Dict[str, AgentResponse], notification_queue: List[str]
) -> None:
    local_notification_queue: List[str] = []

    def subscribing_handler(notification: str) -> None:
        local_notification_queue.append(notification)

    basic_agent_data = agent_registry.get_first_agent_of_type(AgentType.BASIC)
    subscriber = Subscriber.from_env(env_prefix=basic_agent_data.metadata.labels["env_prefix"])
    owner_address = get_owner_agent_address(agent_registry, agent_map)
    subscriber.new_job(owner_address, subscribing_handler, background=True).start()

    time.sleep(1.0)
    assert_notification_queues(publisher_queue=notification_queue, subscriber_queue=local_notification_queue)


@pytest.mark.order(4)
@pytest.mark.usefixtures("agent_flask_apps")
def test_subscribing_as_user(
    agent_registry: AgentRegistry, agent_map: Dict[str, AgentResponse], notification_queue: List[str]
) -> None:
    local_notification_queue: List[str] = []

    def subscribing_handler(notification: str) -> None:
        local_notification_queue.append(notification)

    subscriber = Subscriber.from_api_key(api_key=os.environ["THEORIQ_API_KEY"])
    owner_address = get_owner_agent_address(agent_registry, agent_map)
    subscriber.new_job(owner_address, subscribing_handler, background=True).start()

    time.sleep(1.0)
    assert_notification_queues(publisher_queue=notification_queue, subscriber_queue=local_notification_queue)


@pytest.mark.order(-1)
@pytest.mark.usefixtures("agent_flask_apps")
def test_deletion(agent_map: Dict[str, AgentResponse], user_manager: DeployedAgentManager) -> None:
    for agent in agent_map.values():
        user_manager.delete_agent(agent.system.id)
