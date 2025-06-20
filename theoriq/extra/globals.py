from contextvars import ContextVar

from theoriq.api.v1alpha2.agent import Agent

# Global variable used to access the current agent context
agent_var: ContextVar[Agent] = ContextVar("agent")
