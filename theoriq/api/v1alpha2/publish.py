from __future__ import annotations

import logging
import threading
from typing import Any, Callable, Dict, Optional

from ...biscuit import AgentAddress
from .agent import Agent
from .protocol import ProtocolClient
from .protocol.biscuit_provider import BiscuitProviderFromPrivateKey

logger = logging.getLogger(__name__)


class PublisherContext:
    def __init__(self, agent: Agent, client: ProtocolClient) -> None:
        self._agent = agent
        self._client = client
        self._address = agent.config.address if agent.virtual_address.is_null else agent.virtual_address
        self._biscuit_provider = BiscuitProviderFromPrivateKey(
            agent.config.private_key, agent.config.address, self._client
        )
        self._configuration: Optional[Dict[str, Any]] = None

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
        logger.info(f"Refreshing configuration for agent {virtual_address}")
        if virtual_address.is_null:
            return

        agent_metadata = self._client.get_agent(virtual_address.address, self._biscuit_provider.get_biscuit())
        if agent_metadata.configuration.virtual:
            self._configuration = agent_metadata.configuration.virtual.configuration
        else:
            logger.warning(f"Agent {virtual_address} has no virtual configuration")


PublishJob = Callable[[PublisherContext], None]

virtual_publishers: Dict[AgentAddress, Publisher] = {}
virtual_publisher_job: Dict[AgentAddress, PublishJob] = {}


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
        virtual_publisher_job[root_agent.config.address] = job
        client = ProtocolClient.from_env()
        biscuit_provider = BiscuitProviderFromPrivateKey(
            root_agent.config.private_key, root_agent.config.address, client
        )
        agents = client.get_agents(biscuit_provider.get_biscuit())
        for agent in agents:
            if agent.configuration.virtual and agent.configuration.virtual.agent_id == root_agent.config.address:
                Publisher.start_or_update_virtual_job(root_agent, AgentAddress(agent.system.id))

    @staticmethod
    def start_or_update_virtual_job(root_agent: Agent, virtual_address: AgentAddress) -> None:
        job = virtual_publisher_job.get(root_agent.config.address, None)
        if job is None:
            return

        publisher = virtual_publishers.get(virtual_address, None)
        if publisher is None:
            new_agent = Agent(root_agent.config, root_agent.schemas)
            new_agent.virtual_address = virtual_address
            publisher = Publisher(new_agent)
            virtual_publishers[new_agent.virtual_address] = publisher
            publisher._context.refresh_configuration()
            publisher.new_job(job, background=True).start()
        else:
            publisher._context.refresh_configuration()
