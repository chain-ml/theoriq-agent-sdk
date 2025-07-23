from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, List, Optional
from uuid import UUID

from pydantic import Field, field_validator

from theoriq.dialog import Dialog, DialogItem, DialogItemPredicate
from theoriq.dialog.block import BaseTheoriqModel
from theoriq.types import SourceType


class ConfigurationRef(BaseTheoriqModel):
    """
    Represents the expected payload for a configuration request.
    """

    hash: str
    id: str


class Configuration(BaseTheoriqModel):
    """
    Represents the expected payload for a configuration request.
    """

    fromRef: ConfigurationRef


class ExecuteRequestBody(BaseTheoriqModel):
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

    def filter_items(self, predicate: DialogItemPredicate) -> List[DialogItem]:
        return self.dialog.filter_items(predicate)

    def last_item_predicate(self, predicate: DialogItemPredicate) -> Optional[DialogItem]:
        return self.dialog.last_item_predicate(predicate)


class RequestItem(BaseTheoriqModel):
    id: UUID
    source: str
    source_type: SourceType
    start_at: datetime
    end_at: Optional[datetime]  # TODO: wasn't optional before?
    target_agent: str

    # TODO: remove after SourceType lowercase fix
    # noinspection PyNestedDecorators
    @field_validator("source_type", mode="before")
    @classmethod
    def validate_source_type(cls, value: Any) -> SourceType:
        return SourceType.from_value(value)


class Request(BaseTheoriqModel):
    body: Optional[ExecuteRequestBody] = None  # could be empty for configure request
    body_bytes: List[int]


class Response(BaseTheoriqModel):
    body: Optional[DialogItem] = None
    body_bytes: Optional[List[int]] = None
    source: Annotated[str, Field(alias="from")]
    message: Optional[str] = None
    status_code: int


class Source(BaseTheoriqModel):
    source: str
    source_type: SourceType

    # TODO: remove after SourceType lowercase fix
    # noinspection PyNestedDecorators
    @field_validator("source_type", mode="before")
    @classmethod
    def validate_source_type(cls, value: Any) -> SourceType:
        return SourceType.from_value(value)


class Event(BaseTheoriqModel):
    context: str
    data: Optional[Any] = None
    event_type: str
    message: str
    timestamp: datetime


class RequestAudit(BaseTheoriqModel):
    id: UUID
    request: Request
    response: Response
    events: List[Event]
