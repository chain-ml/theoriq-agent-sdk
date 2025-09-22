import itertools
import time
from concurrent.futures import thread
from typing import Optional
from unittest.mock import MagicMock

import pytest
from theoriq.api.v1alpha2 import ProtocolClient
from theoriq.api.v1alpha2.protocol.biscuit_provider import BiscuitProvider
from theoriq.api.v1alpha2.subscribe import Subscriber, SubscriberStopException
from theoriq.biscuit import AgentAddress


@pytest.mark.timeout(10)
def test_subscribe_job_handle_exception() -> None:
    biscuit_provider = MagicMock(spec=BiscuitProvider)
    client = MagicMock(spec=ProtocolClient)
    client.subscribe_to_agent_notifications.side_effect = [["first"], ValueError, ["something"], SubscriberStopException]
    subscriber = Subscriber(biscuit_provider, client)

    actual: Optional[str] = None
    def handler(message: str) -> None:
        nonlocal actual
        actual = message

    job = subscriber.new_job(AgentAddress.one(), handler, background=True)
    job.run()
    time.sleep(4)

    assert not job.is_alive()
    assert actual == "something"
