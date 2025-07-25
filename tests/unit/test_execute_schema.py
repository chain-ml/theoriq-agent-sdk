import json
from typing import Literal, Optional

from pydantic import BaseModel

from theoriq.api.v1alpha2.schemas import ExecuteSchema
from theoriq.dialog import BaseTheoriqModel, BlockBase, CommandBlock, UnknownBlock
from theoriq.dialog.command_items import CommandData


class AddCommandArguments(BaseTheoriqModel):
    """Arguments for addition command."""

    a: int
    b: int

class MulCommandArguments(BaseTheoriqModel):
    """Arguments for addition command."""

    c: int
    d: int


class AddCommandResponse(BaseTheoriqModel):
    result: int


def test_execute_schema_from_base_models() -> None:
    execute_schema = ExecuteSchema.from_base_models(request_types=CommandBlock[AddCommandArguments, Literal["add"]], response_types=BlockBase[AddCommandResponse, Literal["addResult"]])

    print(execute_schema.model_dump_json(indent=2))

def test_execute_schema_add_mul_commands() -> None:
    request_types =  [
        CommandBlock[AddCommandArguments, Literal["add"]],
        CommandBlock[MulCommandArguments, Literal["mul", "div"]],
    ]

    response_types = BlockBase[AddCommandResponse, Literal["computeResult"]]
    execute_schema = ExecuteSchema.from_base_models(request_types, response_types)

    print(execute_schema.model_dump_json(indent=2))