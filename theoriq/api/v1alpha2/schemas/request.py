from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

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
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: UUID
    source: str
    source_type: SourceType
    start_at: datetime
    end_at: datetime
    target_agent: str

    # TODO: remove after SourceType lowercase fix
    # noinspection PyNestedDecorators
    @field_validator("source_type", mode="before")
    @classmethod
    def validate_source_type(cls, value: Any) -> SourceType:
        return SourceType.from_value(value)


class Request(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    body: Optional[ExecuteRequestBody] = None  # could be empty for configure request
    body_bytes: List[int]


class Response(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    body: Optional[Dict[str, Any]] = None  # TODO: must be a DialogItem
    body_bytes: Optional[List[int]] = None
    source: Annotated[str, Field(alias="from")]
    message: Optional[str] = None
    status_code: int


class Source(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    source: str
    source_type: SourceType

    # TODO: remove after SourceType lowercase fix
    # noinspection PyNestedDecorators
    @field_validator("source_type", mode="before")
    @classmethod
    def validate_source_type(cls, value: Any) -> SourceType:
        return SourceType.from_value(value)


class Event(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    context: str
    data: Optional[Any] = None
    event_type: str
    message: str
    timestamp: datetime


class RequestAudit(BaseModel):
    id: UUID
    request: Request
    response: Response
    events: List[Event]
