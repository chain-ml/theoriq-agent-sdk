from typing import Literal, Optional

from pydantic import BaseModel

from theoriq.api.v1alpha2.schemas import ExecuteSchema


class AddCommandArguments(BaseModel):
    """Arguments for addition command."""

    a: int
    b: int


class CommandDataAdd(BaseModel):
    """Command data for addition operation."""

    name: Literal["add"]
    arguments: AddCommandArguments


class AddCommand(BaseModel):
    """Addition command structure."""

    type: Literal["command"]
    data: CommandDataAdd
    key: Optional[str] = None
    ref: Optional[str] = None


class AddCommandResponse(BaseModel):
    result: int


def test_execute_schema_from_base_models() -> None:
    execute_schema = ExecuteSchema.from_base_models(request=AddCommand, response=AddCommandResponse)
