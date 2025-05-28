from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import List, Sequence

from theoriq.types import AgentDataObject


class AgentType(str, Enum):
    """Agent types for test agents."""

    CHILD = "child"
    """Non-configurable agent. Also used as subscriber."""

    PARENT = "parent"
    """Non-configurable agent that can register other agents. Also used as publisher."""

    CONFIGURABLE = "configurable"
    """Configurable agent."""


class AgentRegistry:
    def __init__(self, agents: Sequence[AgentDataObject]) -> None:
        self.agents = list(agents)

    @classmethod
    def from_dir(cls, data_dir: str) -> AgentRegistry:
        yaml_files = [str(f) for f in Path(data_dir).rglob("*.yaml")]
        agents = [AgentDataObject.from_yaml(yaml_file) for yaml_file in yaml_files]
        return cls(agents)

    def get_agents_of_type(self, agent_type: AgentType) -> List[AgentDataObject]:
        return [agent for agent in self.agents if agent.metadata.labels["agent_type"] == agent_type.value]

    def get_agents_of_types(self, agent_types: Sequence[AgentType]) -> List[AgentDataObject]:
        return [agent for agent_type in agent_types for agent in self.get_agents_of_type(agent_type)]
