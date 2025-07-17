from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from theoriq.dialog import Dialog, DialogItem, DialogItemPredicate
from theoriq.types import SourceType


class ConfigurationRef(BaseModel):
    """
    Represents the expected payload for a configuration request.
    """

    hash: str
    id: str


class Configuration(BaseModel):
    """
    Represents the expected payload for a configuration request.
    """

    fromRef: ConfigurationRef


class ExecuteRequestBody(BaseModel):
    """
    A class representing the body of an execute request. Inherits from BaseModel.
    """

    configuration: Optional[Configuration] = None
    dialog: Dialog

    @property
    def last_item(self) -> Optional[DialogItem]:
        return self.dialog.last_item

    @property
    def last_text(self) -> str:
        return self.dialog.last_text

    def last_item_from(self, source_type: SourceType) -> Optional[DialogItem]:
        return self.dialog.last_item_from(source_type)

    def last_item_predicate(self, predicate: DialogItemPredicate) -> Optional[DialogItem]:
        return self.dialog.last_item_predicate(predicate)


class RequestItem(BaseModel):
    id: UUID
    source: str
    source_type: Annotated[SourceType, Field(alias="sourceType")]
    start_at: Annotated[datetime, Field(alias="startAt")]
    end_at: Annotated[datetime, Field(alias="endAt")]
    target_agent: Annotated[str, Field(alias="targetAgent")]

    # noinspection PyNestedDecorators
    @field_validator("source_type", mode="before")
    @classmethod
    def validate_source_type(cls, value: Any) -> SourceType:
        return SourceType.from_value(value)


class Request(BaseModel):
    body: ExecuteRequestBody
    body_bytes: Annotated[List[int], Field(alias="bodyBytes")]


class Response(BaseModel):
    body: Dict[str, Any]  # TODO: must be a DialogItem
    body_bytes: Annotated[List[int], Field(alias="bodyBytes")]
    source: Annotated[str, Field(alias="from")]
    message: Optional[str] = None
    status_code: Annotated[int, Field(alias="statusCode")]


class Source(BaseModel):
    source: Annotated[str, Field(alias="sourceId")]
    source_type: Annotated[SourceType, Field(alias="sourceType")]

    # noinspection PyNestedDecorators
    @field_validator("source_type", mode="before")
    @classmethod
    def validate_source_type(cls, value: Any) -> SourceType:
        return SourceType.from_value(value)


class Event(BaseModel):
    context: str
    data: Optional[Any] = None
    event_type: Annotated[str, Field(alias="eventType")]
    message: str
    timestamp: Annotated[datetime, Field(alias="timestamp")]


class RequestAudit(BaseModel):
    id: UUID
    request: Request
    response: Response
    events: List[Event]
