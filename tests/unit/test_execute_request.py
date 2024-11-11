from theoriq.schemas import ExecuteRequestBody
from theoriq.types import SourceType

request_payload = {
    "dialog": {
        "items": [
            {
                "sourceType": "user",
                "source": "0x30fBa3e4195D17d06Ea9740338c8cdc9611468A9",
                "timestamp": "2024-11-10T11:06:01Z",
                "blocks": [{"data": {"text": "I am looking to get the latest news on memecoins?"}, "type": "text"}],
                "requestId": ["21a110d6-f63c-431a-8583-ff6d8e0b29cf"],
                "dialogId": "acfe3d3c-9cc3-425a-bd29-fca317d58a9f",
                "sse": [],
            },
            {
                "blocks": [
                    {"data": {"text": "The recommended agent is News Search -- A news search agent. "}, "type": "text"}
                ],
                "source": "a271094f9b32aa6fb20c8de5e6cdb06e41603415fc749c7a43e46d5875f93c9f",
                "sourceType": "agent",
                "timestamp": "2024-11-10T04:06:05.977921+00:00",
                "requestId": "21a110d6-f63c-431a-8583-ff6d8e0b29cf",
                "sse": [],
                "dialogId": "54112b32-4e8a-4111-aa49-a631b3e142db",
            },
            {
                "sourceType": "user",
                "source": "0x30fBa3e4195D17d06Ea9740338c8cdc9611468A9",
                "timestamp": "2024-11-11T10:38:36",
                "blocks": [{"data": {"text": "I am looking to get the latest news on memecoins?"}, "type": "text"}],
                "requestId": [],
                "dialogId": "f2e5623f-f9a2-4fbe-a60d-2339d176fa41",
                "sse": [],
            },
        ]
    }
}


def test_exec_request_body_deserialization():

    e: ExecuteRequestBody = ExecuteRequestBody.model_validate(request_payload)
    assert isinstance(e, ExecuteRequestBody)


def test_last_item_with_different_formats():
    e: ExecuteRequestBody = ExecuteRequestBody.model_validate(request_payload)
    li = e.last_item
    assert li is not None
    assert li.source == "0x30fBa3e4195D17d06Ea9740338c8cdc9611468A9"

def test_last_item_from():
    e: ExecuteRequestBody = ExecuteRequestBody.model_validate(request_payload)
    li = e.last_item_from(SourceType.Agent)
    assert li is not None
    assert li.source == "a271094f9b32aa6fb20c8de5e6cdb06e41603415fc749c7a43e46d5875f93c9f"
