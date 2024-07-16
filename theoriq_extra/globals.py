from contextvars import ContextVar

from theoriq.agent import Agent
from theoriq.facts import TheoriqCost
from theoriq.schemas import ExecuteRequest

# Global variable used to access the current agent context
agent_var: ContextVar[Agent] = ContextVar("agent")

# Global variable used to access the execute request context
execute_request_var: ContextVar[ExecuteRequest] = ContextVar("execute_request")

# Global variable used to set the cost of an executed request
execute_response_cost_var: ContextVar[TheoriqCost] = ContextVar("theoriq_cost", default=TheoriqCost.zero("USDC"))
