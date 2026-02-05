import os
import time
from typing import Any, Dict, Generator, List

import pytest
from tests.integration.agent_registry import AgentRegistry, AgentType
from tests.integration.agent_runner import TestConfig

from theoriq.api.v1alpha2 import AgentResponse
from theoriq.api.v1alpha2.manage import AgentManager
from theoriq.api.v1alpha2.protocol.biscuit_provider import BiscuitProviderFactory
from theoriq.api.v1alpha2.publish import Publisher, PublisherContext
from theoriq.api.v1alpha2.schemas import VirtualAgentNotification
from theoriq.api.v1alpha2.subscribe import Subscriber, VirtualSubscribeHandlerFn, VirtualSubscriber
from theoriq.biscuit import AgentAddress
from theoriq.types import AgentConfiguration, AgentMetadata


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


def get_configurable_agent(agent_registry: AgentRegistry, agent_map: Dict[str, AgentResponse]) -> AgentResponse:
    configurable_agent_data = agent_registry.get_first_agent_of_type(AgentType.CONFIGURABLE)
    configurable_name = configurable_agent_data.spec.metadata.name
    return next(agent for agent in agent_map.values() if agent.metadata.name == configurable_name)


@pytest.mark.order(1)
@pytest.mark.usefixtures("agent_flask_apps")
def test_registration(
    agent_registry: AgentRegistry, agent_map: Dict[str, AgentResponse], user_manager: AgentManager
) -> None:
    agent_data_objs = agent_registry.get_agents_of_types([AgentType.OWNER, AgentType.BASIC, AgentType.CONFIGURABLE])
    for agent_data in agent_data_objs:
        agent = user_manager.create_agent_from_spec(agent_data.spec)
        agent_map[agent.system.id] = agent


@pytest.mark.order(2)
@pytest.mark.usefixtures("agent_flask_apps")
def test_configuration(
    agent_registry: AgentRegistry, agent_map: Dict[str, AgentResponse], user_manager: AgentManager
) -> None:
    configurable_agent = get_configurable_agent(agent_registry, agent_map)

    for i in range(1, 3):
        metadata = AgentMetadata(
            name=f"Virtual Subscriber Agent #{i}",
            short_description=f"Subscriber short description #{i}",
            long_description=f"Subscriber long description #{i}",
        )
        config = TestConfig(text=f"Subscriber config #{i}", number=i * 100)
        configuration = AgentConfiguration.for_virtual(
            agent_id=configurable_agent.system.id, configuration=config.model_dump()
        )

        agent = user_manager.create_agent(metadata, configuration)
        assert agent.configuration.is_virtual
        agent_map[agent.system.id] = agent


@pytest.mark.order(3)
@pytest.mark.usefixtures("agent_flask_apps")
def test_publishing(agent_registry: AgentRegistry, notification_queue: List[str]) -> None:
    def publishing_job(context: PublisherContext) -> None:
        i = 0
        while i < 1_000:
            notification = f"Sample notification #{i}"
            notification_queue.append(notification)
            context.publish(notification)

            i += 1
            time.sleep(0.3)

    owner_agent_data = agent_registry.get_first_agent_of_type(AgentType.OWNER)
    publisher = Publisher.from_env(env_prefix=owner_agent_data.metadata.labels["env_prefix"])
    publisher.new_job(job=publishing_job, background=True).start()


@pytest.mark.order(4)
@pytest.mark.usefixtures("agent_flask_apps")
def test_subscribing_as_agent(
    agent_registry: AgentRegistry, agent_map: Dict[str, AgentResponse], notification_queue: List[str]
) -> None:
    local_notification_queue: List[str] = []

    def subscribing_handler(message: str) -> None:
        local_notification_queue.append(message)

    basic_agent_data = agent_registry.get_first_agent_of_type(AgentType.BASIC)
    subscriber = Subscriber.from_env(env_prefix=basic_agent_data.metadata.labels["env_prefix"])
    owner_address = get_owner_agent_address(agent_registry, agent_map)
    subscriber.new_job(owner_address, subscribing_handler, background=True).start()

    time.sleep(1.0)
    assert_notification_queues(publisher_queue=notification_queue, subscriber_queue=local_notification_queue)


@pytest.mark.order(5)
@pytest.mark.usefixtures("agent_flask_apps")
def test_subscribing_as_user(
    agent_registry: AgentRegistry, agent_map: Dict[str, AgentResponse], notification_queue: List[str]
) -> None:
    local_notification_queue: List[str] = []

    def subscribing_handler(message: str) -> None:
        local_notification_queue.append(message)

    subscriber = Subscriber.from_api_key(api_key=os.environ["THEORIQ_API_KEY"])
    owner_address = get_owner_agent_address(agent_registry, agent_map)
    subscriber.new_job(owner_address, subscribing_handler, background=True).start()

    time.sleep(1.0)
    assert_notification_queues(publisher_queue=notification_queue, subscriber_queue=local_notification_queue)


@pytest.mark.order(6)
@pytest.mark.usefixtures("agent_flask_apps")
def test_subscribing_as_virtual_agents(
    agent_registry: AgentRegistry, agent_map: Dict[str, AgentResponse], notification_queue: List[str]
) -> None:
    virtual_agents = [agent for agent in agent_map.values() if agent.configuration.is_virtual]
    assert len(virtual_agents) == 2

    def make_handler(name: str, expected: Dict[str, Any], queue: List[str]) -> VirtualSubscribeHandlerFn:
        def subscribing_handler(notification: VirtualAgentNotification) -> None:
            print(f"Got notification {notification} as {name}")
            assert notification.configuration == expected

            parsed_config = notification.try_parse_configuration(TestConfig)
            assert parsed_config is not None
            assert parsed_config.text == expected["text"]
            assert parsed_config.number == expected["number"]

            queue.append(notification.notification)

        return subscribing_handler

    owner_address = get_owner_agent_address(agent_registry, agent_map)

    for virtual_agent in virtual_agents:
        local_notification_queue: List[str] = []
        expected_config = virtual_agent.configuration.ensure_virtual.configuration

        biscuit_provider = BiscuitProviderFactory.from_api_key(api_key=os.environ["THEORIQ_API_KEY"])
        subscriber = VirtualSubscriber(biscuit_provider, virtual_agent_address=AgentAddress(virtual_agent.system.id))
        handler = make_handler(virtual_agent.metadata.name, expected_config, local_notification_queue)
        subscriber.new_job(owner_address, handler, background=True).start()

        time.sleep(1.0)
        assert_notification_queues(publisher_queue=notification_queue, subscriber_queue=local_notification_queue)


@pytest.mark.order(-1)
@pytest.mark.usefixtures("agent_flask_apps")
def test_deletion(agent_map: Dict[str, AgentResponse], user_manager: AgentManager) -> None:
    for agent in agent_map.values():
        user_manager.delete_agent(agent.system.id)
