from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Type, List, Union

from pydantic import BaseModel, RootModel

from theoriq.dialog import BlockBase


BlockTypes = Union[Type[BlockBase[Any, Any]], Sequence[Type[BlockBase[Any, Any]]]]

class ExecuteSchema(BaseModel):
    """
    Represents a schema for an execute request.

    Attributes:
        request: JSON schema for the request
        response: JSON schema for the response
    """

    request: Dict[str, Any]
    response: Dict[str, Any]

    @classmethod
    def from_base_models(cls, request_types: BlockTypes, response_types: BlockTypes) -> ExecuteSchema:
        request = Union[tuple(request_types)] if isinstance(request_types, list) else request_types
        response = Union[tuple(response_types)] if isinstance(response_types, list) else response_types
        return cls(
            request=RootModel[List[request]].model_json_schema(),
            response=RootModel[List[response]].model_json_schema(),
        )


class AgentSchemas(BaseModel):
    """
    Represents the schemas supported by an agent.

    Attributes:
        execute: Optional mapping of operation names to their execute schemas; for agents supporting execute requests
        notification: Optional JSON schema for notifications; for publisher agents
        configuration: Optional JSON schema for agent configuration; for configurable agents
    """

    execute: Optional[Dict[str, ExecuteSchema]] = None
    notification: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None

    @classmethod
    def empty(cls) -> AgentSchemas:
        return AgentSchemas(configuration=None, notification=None, execute=None)
