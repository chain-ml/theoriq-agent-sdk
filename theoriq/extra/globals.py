from contextvars import ContextVar

from theoriq import Agent

# Global variable used to access the current agent context
agent_var: ContextVar[Agent] = ContextVar("agent")
