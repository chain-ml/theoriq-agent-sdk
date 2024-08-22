from theoriq.schemas import DialogItem, ExecuteRequestBody, TextItemBlock
from theoriq.schemas.request import Dialog


def test_schemas():
    request_body = {
        "dialog": {
            "items": [
                {
                    "timestamp": "2024-08-07T00:00:00.000000+00:00",
                    "sourceType": "user",
                    "source": "0x012345689abcdef0123456789abcdef012345689abcdef0123456789abcdef01234567",
                    "blocks": [
                        {
                            "data": {
                                "items": [
                                    {"name": "route1", "score": 0.73},
                                    {"name": "route2", "score": 0.27, "reason": "not the best route"},
                                ]
                            },
                            "type": "router",
                        },
                        {"data": {"text": "My name is John Doe"}, "type": "text"},
                        {"data": {"code": "import numpy"}, "type": "code:python"},
                        {
                            "type": "metrics",
                            "data": {
                                "items": [
                                    {"name": "accuracy", "value": 0.95, "trendPercentage": 0.05},
                                    {"name": "precision", "value": 0.85, "trendPercentage": 0.15},
                                    {"name": "recall", "value": 0.75, "trendPercentage": 0.25},
                                ]
                            },
                        },
                    ],
                }
            ]
        }
    }

    req = ExecuteRequestBody.model_validate(request_body)
    dialog_item = req.dialog.items[0]
    assert dialog_item.blocks[0].data[0].name == "route1"
    assert dialog_item.blocks[0].data[1].score == 0.27
    assert dialog_item.blocks[0].data[1].reason == "not the best route"

    assert dialog_item.blocks[1].data.text == "My name is John Doe"

    assert dialog_item.blocks[2].data.code == "import numpy"

    assert dialog_item.blocks[3].data[-1].trend_percentage == 0.25


def test_serialization():
    dialog = Dialog(
        items=[
            DialogItem.new(
                source="0x012345689abcdef0123456789abcdef012345689abcdef0123456789abcdef01234567",
                blocks=[TextItemBlock(text="Hello World")],
            )
        ]
    )

    dump = dialog.model_dump_json()
    assert dump.startswith('{"items"')
