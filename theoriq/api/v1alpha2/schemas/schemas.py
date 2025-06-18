from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel


class ExecuteSchema(BaseModel):
    """
    Represents a schema for an execute operation.

    Attributes:
        request: JSON schema for the request
        response: JSON schema for the response
    """

    request: Dict[str, Any]
    response: Dict[str, Any]


class AgentSchemas(BaseModel):
    """
    Represents the schemas supported by an agent.

    Attributes:
        configuration: Optional JSON schema for agent configuration
        notification: Optional JSON schema for notifications
        execute: Optional mapping of operation names to their execute schemas
    """

    configuration: Optional[Dict[str, Any]] = None
    notification: Optional[Dict[str, Any]] = None
    execute: Optional[Dict[str, ExecuteSchema]] = None

    @classmethod
    def empty(cls) -> AgentSchemas:
        return AgentSchemas(configuration=None, notification=None, execute=None)

    def set_configuration(self, schema: Dict[str, Any]) -> None:
        self.configuration = schema

    def set_notification(self, schema: Dict[str, Any]) -> None:
        self.notification = schema

    def set_execute(self, schema_map: Dict[str, ExecuteSchema]) -> None:
        self.execute = schema_map

    def add_execute(self, key: str, schema: ExecuteSchema) -> None:
        if self.execute is None:
            self.execute = {}
        self.execute[key] = schema
