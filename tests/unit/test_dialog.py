from uuid import uuid4

from theoriq.schemas import ExecuteRequestBody, Dialog
from theoriq.biscuit import AgentAddress
from theoriq.types import SourceType

dialog_payload = {
        "items": [
            {
                "sourceType": str(SourceType.User),
                "source": AgentAddress.one(),
                "timestamp": "2024-11-04T20:00:39Z",
                "blocks": [
                    {
                        "data": {
                            "text": "Give me the trending tokens in the last 24 hours"
                        },
                        "type": "text"
                    }
                ],
                "requestId": [
                    uuid4()
                ],
                "sse": []
            }
        ]
}


def test_dialog_deserialization():
    d: Dialog = Dialog.model_validate(dialog_payload)
    assert isinstance(d, Dialog)
    assert d.items[0].source_type == SourceType.User
    assert next(iter(d.items[0].find_blocks_of_type("text"))).data.text == "Give me the trending tokens in the last 24 hours"

def test_exec_request_body_deserialization():
    request_body = { "dialog": dialog_payload }
    e: ExecuteRequestBody = ExecuteRequestBody.model_validate(request_body)
    assert isinstance(e, ExecuteRequestBody)