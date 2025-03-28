import threading
from typing import Callable, Optional

from theoriq import Agent
from theoriq.api.v1alpha2 import ProtocolClient
from theoriq.api.v1alpha2.protocol.biscuit_provider import BiscuitProviderFromPrivateKey


class PublisherContext:
    def __init__(self, agent: Agent, client: ProtocolClient) -> None:
        self._agent = agent
        self._client = client
        self._address = agent.config.address if agent.virtual_address.is_null else agent.virtual_address
        self._biscuit_provider = BiscuitProviderFromPrivateKey(agent.config.private_key, self._address, self._client)

    def publish(self, message: str) -> None:
        biscuit = self._biscuit_provider.get_biscuit()
        self._client.post_notification(biscuit, self._address, message)


PublishJob = Callable[[PublisherContext], None]


class Publisher:
    def __init__(self, agent: Agent, client: Optional[ProtocolClient] = None) -> None:
        self._context = PublisherContext(agent, client or ProtocolClient.from_env())

    def new_job(self, job: PublishJob) -> threading.Thread:
        return threading.Thread(target=lambda: job(self._context))
