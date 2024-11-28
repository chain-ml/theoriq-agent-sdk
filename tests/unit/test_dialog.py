from uuid import uuid4

from theoriq.biscuit import AgentAddress
from theoriq.dialog import Dialog
from theoriq.types import SourceType

dialog_payload = {
    "items": [
        {
            "sourceType": str(SourceType.User),
            "source": AgentAddress.one(),
            "timestamp": "2024-11-04T20:00:39Z",
            "blocks": [{"data": {"text": "Give me the trending tokens in the last 24 hours"}, "type": "text"}],
            "requestId": [uuid4()],
            "sse": [],
        },
        {
            "sourceType": str(SourceType.Agent),
            "source": AgentAddress.random(),
            "timestamp": "2024-11-27T00:57:29.725500Z",
            "blocks": [{"data": {"text": "The trending tokens in the last 24 hours are ...."}, "type": "text"}],
            "requestId": [],
            "dialogId": "7f105329-a491-4f6f-8882-67627acce6bb",
            "sse": [],
        },
    ]
}


def test_dialog_deserialization():
    d: Dialog = Dialog.model_validate(dialog_payload)
    assert isinstance(d, Dialog)
    assert d.items[0].source_type == SourceType.User
    assert (
        next(iter(d.items[0].find_blocks_of_type("text"))).data.text
        == "Give me the trending tokens in the last 24 hours"
    )
