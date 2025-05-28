from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from typing import Dict, List, Sequence

from theoriq.types import AgentDataObject

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Agent types for test agents."""

    CHILD = "child"
    """Non-configurable agent. Also used as subscriber."""

    PARENT = "parent"
    """Non-configurable agent that can register other agents. Also used as publisher."""

    CONFIGURABLE = "configurable"
    """Configurable agent."""


# TODO: test this
class AgentRegistry:
    def __init__(self, agents: Sequence[AgentDataObject]) -> None:
        self._agents: Dict[str, AgentDataObject] = {agent.spec.metadata.name: agent for agent in agents}

    @property
    def agents(self) -> Dict[str, AgentDataObject]:
        return self._agents

    @classmethod
    def from_dir(cls, data_dir: str) -> AgentRegistry:
        yaml_files = [str(f) for f in Path(data_dir).rglob("*.yaml")]
        agents = [AgentDataObject.from_yaml(yaml_file) for yaml_file in yaml_files]
        return cls(agents)

    def get_agents_by_type(self, agent_type: AgentType) -> List[AgentDataObject]:
        return [agent for agent in self._agents.values() if agent.metadata.labels["agent_type"] == agent_type.value]

    def get_child_agents(self) -> List[AgentDataObject]:
        return self.get_agents_by_type(AgentType.CHILD)

    def get_parent_agents(self) -> List[AgentDataObject]:
        return self.get_agents_by_type(AgentType.PARENT)

    def get_deployed_agents(self) -> List[AgentDataObject]:
        return self.get_child_agents() + self.get_parent_agents()

    def get_configurable_agents(self) -> List[AgentDataObject]:
        return self.get_agents_by_type(AgentType.CONFIGURABLE)

    def get_env_prefix(self, agent_name: str) -> str:
        return self._agents[agent_name].metadata.labels["env_prefix"]
    
    def get_first_parent_agent_env_prefix(self) -> str:
        first_parent_agent = self.get_parent_agents()[0]
        return self.get_env_prefix(first_parent_agent.spec.metadata.name)

    def get_first_child_agent_env_prefix(self) -> str:
        first_child_agent = self.get_child_agents()[0]
        return self.get_env_prefix(first_child_agent.spec.metadata.name)