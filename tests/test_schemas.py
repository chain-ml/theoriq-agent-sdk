from theoriq.schemas import ExecuteRequestBody


def test_schemas():
    request_body = {
        "dialog": {
            "items": [
                {
                    "timestamp": "123",
                    "sourceType": "user",
                    "source": "0x012345689abcdef0123456789abcdef012345689abcdef0123456789abcdef01234567",
                    "blocks": [
                        {
                            "data": {"items": [{"name": "route1", "score": 0.73}, {"name": "route2", "score": 0.27}]},
                            "type": "router",
                        },
                        {"data": {"text": "My name is John Doe"}, "type": "text"},
                        {"data": {"code": "import numpy"}, "type": "code:python"},
                    ],
                }
            ]
        }
    }

    req = ExecuteRequestBody.model_validate(request_body)
    dialog_item = req.dialog.items[0]
    assert dialog_item.blocks[0].data[0].name == "route1"
    assert dialog_item.blocks[0].data[1].score == 0.27
    assert dialog_item.blocks[1].data.text == "My name is John Doe"
    assert dialog_item.blocks[2].data.code == "import numpy"
