import time
from typing import Optional
from unittest.mock import MagicMock

import pytest

from theoriq.api.v1alpha2 import ProtocolClient
from theoriq.api.v1alpha2.protocol.biscuit_provider import BiscuitProvider
from theoriq.api.v1alpha2.schemas import VirtualAgentNotification
from theoriq.api.v1alpha2.subscribe import Subscriber, SubscriberStopException, VirtualSubscriber
from theoriq.biscuit import AgentAddress


def _create_mock_agent_response(configuration_hash: Optional[str]) -> MagicMock:
    """Create a mock AgentResponse for testing, virtual if configuration hash is not None."""
    mock_response = MagicMock()
    mock_response.configuration.virtual = None
    if configuration_hash is not None:
        mock_virtual = MagicMock()
        mock_virtual.configuration_hash = configuration_hash
        mock_response.configuration.virtual = mock_virtual
    return mock_response


@pytest.mark.timeout(10)
def test_subscribe_job_handle_exception() -> None:
    biscuit_provider = MagicMock(spec=BiscuitProvider)
    client = MagicMock(spec=ProtocolClient)
    client.subscribe_to_agent_notifications.side_effect = [
        ["first"],
        ValueError,
        ["something"],
        SubscriberStopException,
    ]
    subscriber = Subscriber(biscuit_provider, client)

    actual: Optional[str] = None

    def handler(message: str) -> None:
        nonlocal actual
        actual = message

    job = subscriber.new_job(AgentAddress.one(), handler, background=True)
    job.run()
    time.sleep(4)

    assert not job.is_alive()
    assert actual is not None
    assert actual == "something"


@pytest.mark.timeout(10)
def test_virtual_subscribe_job_receive_config() -> None:
    subscriber_config = {"text": "subscriber config", "number": 42}
    config_hash = "abc123hash"
    virtual_agent_address = AgentAddress.random()

    biscuit_provider = MagicMock(spec=BiscuitProvider)
    client = MagicMock(spec=ProtocolClient)
    client.subscribe_to_agent_notifications.side_effect = [
        ["notification"],
        SubscriberStopException,
    ]
    # get_agent returns the configuration hash for virtual agents
    client.get_agent.return_value = _create_mock_agent_response(configuration_hash=config_hash)
    # get_configuration returns the config
    client.get_configuration.return_value = subscriber_config
    subscriber = VirtualSubscriber(biscuit_provider, virtual_agent_address=virtual_agent_address, client=client)

    actual: Optional[VirtualAgentNotification] = None

    def handler(message: VirtualAgentNotification) -> None:
        nonlocal actual
        actual = message

    job = subscriber.new_job(AgentAddress.one(), handler, background=True)
    job.run()
    time.sleep(2)

    assert not job.is_alive()
    assert actual is not None
    assert actual.notification == "notification"
    assert actual.configuration == subscriber_config

    # verify get_agent was called with subscriber's address to get the hash
    client.get_agent.assert_called_with(virtual_agent_address, biscuit_provider.get_biscuit())
    # verify get_configuration was called with the hash (uses caching)
    client.get_configuration.assert_called()
