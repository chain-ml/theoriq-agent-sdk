from __future__ import annotations

import threading
from typing import Any, Callable, Dict, Optional, Sequence

from .agent import Agent
from .protocol import ProtocolClient
from .protocol.biscuit_provider import BiscuitProviderFromPrivateKey
from ...biscuit import AgentAddress


class PublisherContext:
    def __init__(self, agent: Agent, client: ProtocolClient) -> None:
        self._agent = agent
        self._client = client
        self._address = agent.config.address if agent.virtual_address.is_null else agent.virtual_address
        self._biscuit_provider = BiscuitProviderFromPrivateKey(agent.config.private_key, agent.config.address, self._client)
        self._configuration: Optional[Dict[str, Any]] = None
        self._configuration_hash: Optional[str] = None

    @classmethod
    def from_env(cls) -> PublisherContext:
        return cls(agent=Agent.from_env(), client=ProtocolClient.from_env())

    def publish(self, message: str) -> None:
        biscuit = self._biscuit_provider.get_biscuit()
        self._client.post_notification(biscuit, self._address.address, message)

    @property
    def configuration(self) -> Optional[Dict[str, Any]]:
        return self._configuration

    def refresh_configuration(self) -> None:
        virtual_address = self._agent.virtual_address
        if virtual_address.is_null:
            return

        agent_metadata = self._client.get_agent(virtual_address.address, self._biscuit_provider.get_biscuit())
        configuration_hash = agent_metadata.configuration.virtual.configuration_hash
        if configuration_hash == self._configuration_hash:
            return

        self._configuration = self._client.get_configuration(
            request_biscuit=self._biscuit_provider.get_biscuit(),
            agent_address=virtual_address,
            configuration_hash=self._configuration_hash,
        )


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

    @staticmethod
    def resume_virtual_jobs(root_agent: Agent, job: PublishJob) -> None:
        client = ProtocolClient.from_env()
        biscuit_provider = BiscuitProviderFromPrivateKey(root_agent.config.private_key, root_agent.config.address, client)
        agents = client.get_agents(biscuit_provider.get_biscuit())
        for agent in agents:
            if agent.configuration.virtual and agent.configuration.virtual.agent_id == root_agent.config.address:
                new_agent = Agent(root_agent.config, root_agent.schemas)
                new_agent.virtual_address = AgentAddress(agent.system.id)
                publisher = Publisher(new_agent)
                publisher._context.refresh_configuration()
                publisher.new_job(job, background=True).start()
