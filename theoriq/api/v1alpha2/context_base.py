from abc import ABC

from theoriq import Agent

from ...types import AgentMetadata
from ...types.agent_data import AgentDescriptions
from ...utils import TTLCache
from . import ProtocolClient


class ContextBase(ABC):
    _metadata_cache: TTLCache[AgentMetadata] = TTLCache(ttl=180, max_size=40)

    def __init__(self, agent: Agent, protocol_client: ProtocolClient):
        """
        Initializes a new instance of Context.

        Args:
            agent (Agent): The agent responsible for handling the work.
        """
        self._agent = agent
        self._protocol_client = protocol_client

    def get_agent_metadata(self, agent_id: str) -> AgentMetadata:
        result = self._metadata_cache.get(agent_id)
        if result is None:
            result = self._get_agent_metadata(agent_id)
            self._metadata_cache.set(agent_id, result)

        return result

    def _get_agent_metadata(self, agent_id: str) -> AgentMetadata:
        agent_response = self._protocol_client.get_agent(agent_id=agent_id)
        metadata = agent_response.metadata
        descriptions = AgentDescriptions(short=metadata.short_description, long=metadata.long_description)
        return AgentMetadata(
            name=metadata.name,
            descriptions=descriptions,
            tags=metadata.tags,
            examples=metadata.example_prompts,
            cost_card=metadata.cost_card,
        )
