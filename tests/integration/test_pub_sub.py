import os
import time
from typing import Dict, List

import pytest
from tests.integration.agent_registry import AgentRegistry

from theoriq.api.v1alpha2 import AgentResponse
from theoriq.api.v1alpha2.manage import DeployedAgentManager
from theoriq.api.v1alpha2.publish import Publisher, PublisherContext
from theoriq.api.v1alpha2.subscribe import Subscriber
from theoriq.biscuit import AgentAddress

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


def get_parent_agent_address(agent_registry: AgentRegistry, agent_map: Dict[str, AgentResponse]) -> AgentAddress:
    parent_agent_data = agent_registry.get_parent_agents()[0]
    maybe_parent_agent = next(
        (agent for agent in agent_map.values() if agent.metadata.name == parent_agent_data.spec.metadata.name), None
    )
    if maybe_parent_agent is None:
        raise RuntimeError("Parent agent data object not found")
    return AgentAddress(maybe_parent_agent.system.id)


@pytest.mark.order(1)
@pytest.mark.usefixtures("agent_flask_apps")
def test_registration(
    agent_registry: AgentRegistry, agent_map: Dict[str, AgentResponse], user_manager: DeployedAgentManager
) -> None:
    for agent_data in agent_registry.get_deployed_agents():
        agent = user_manager.create_agent(
            metadata=agent_data.spec.metadata, configuration=agent_data.spec.configuration
        )
        print(f"Successfully registered `{agent.metadata.name}` with id=`{agent.system.id}`\n")
        agent_map[agent.system.id] = agent


@pytest.mark.order(2)
@pytest.mark.usefixtures("agent_flask_apps")
def test_publishing(agent_registry: AgentRegistry) -> None:
    """Parent agent is a publisher."""
    parent_agent_data = agent_registry.get_parent_agents()[0]
    publisher = Publisher.from_env(env_prefix=agent_registry.get_env_prefix(parent_agent_data.spec.metadata.name))
    publisher.new_job(job=publishing_job, background=True).start()


@pytest.mark.order(3)
@pytest.mark.usefixtures("agent_flask_apps")
def test_subscribing_as_agent(agent_registry: AgentRegistry, agent_map: Dict[str, AgentResponse]) -> None:
    """Child agent is a subscriber."""

    agent_notification_queue_sub: List[str] = []

    def subscribing_handler(notification: str) -> None:
        agent_notification_queue_sub.append(notification)

    child_agent_data = agent_registry.get_child_agents()[0]
    subscriber = Subscriber.from_env(env_prefix=agent_registry.get_env_prefix(child_agent_data.spec.metadata.name))
    subscriber.new_job(
        agent_address=get_parent_agent_address(agent_registry, agent_map), handler=subscribing_handler, background=True
    ).start()

    time.sleep(1.0)
    assert_notification_queues(agent_notification_queue_sub)


@pytest.mark.order(4)
@pytest.mark.usefixtures("agent_flask_apps")
def test_subscribing_as_user(agent_registry: AgentRegistry, agent_map: Dict[str, AgentResponse]) -> None:
    """User is a subscriber."""

    user_notification_queue_sub: List[str] = []

    def subscribing_handler(notification: str) -> None:
        user_notification_queue_sub.append(notification)

    subscriber = Subscriber.from_api_key(api_key=os.environ["THEORIQ_API_KEY"])
    subscriber.new_job(
        agent_address=get_parent_agent_address(agent_registry, agent_map), handler=subscribing_handler, background=True
    ).start()

    time.sleep(1.0)
    assert_notification_queues(user_notification_queue_sub)


@pytest.mark.order(-1)
@pytest.mark.usefixtures("agent_flask_apps")
def test_deletion(agent_map: Dict[str, AgentResponse], user_manager: DeployedAgentManager) -> None:
    for agent in agent_map.values():
        user_manager.delete_agent(agent.system.id)
        print(f"Successfully deleted `{agent.system.id}`\n")
