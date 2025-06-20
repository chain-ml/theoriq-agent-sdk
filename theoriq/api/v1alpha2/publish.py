from __future__ import annotations

import threading
from typing import Callable, Optional

from .agent import Agent
from .protocol import ProtocolClient
from .protocol.biscuit_provider import BiscuitProviderFromPrivateKey


class PublisherContext:
    def __init__(self, agent: Agent, client: ProtocolClient) -> None:
        self._agent = agent
        self._client = client
        self._address = agent.config.address if agent.virtual_address.is_null else agent.virtual_address
        self._biscuit_provider = BiscuitProviderFromPrivateKey(agent.config.private_key, self._address, self._client)

    @classmethod
    def from_env(cls) -> PublisherContext:
        return cls(agent=Agent.from_env(), client=ProtocolClient.from_env())

    def publish(self, message: str) -> None:
        biscuit = self._biscuit_provider.get_biscuit()
        self._client.post_notification(biscuit, self._address.address, message)


PublishJob = Callable[[PublisherContext], None]


class Publisher:
    """Manages publishing messages from an agent its notification channel."""

    def __init__(self, agent: Agent, client: Optional[ProtocolClient] = None) -> None:
        self._context = PublisherContext(agent=agent, client=client or ProtocolClient.from_env())

    @classmethod
    def from_env(cls, env_prefix: str = "") -> Publisher:
        return cls(agent=Agent.from_env(env_prefix=env_prefix), client=ProtocolClient.from_env())

    def new_job(self, job: PublishJob, background: bool = False) -> threading.Thread:
        """
        Create a new job to publish messages.

        Args:
            job: The function to execute when publishing a message
            background: Whether to run the job in the background

        Returns:
            A thread object that can be started to run the publish job
        """
        return threading.Thread(target=lambda: job(self._context), daemon=background)
