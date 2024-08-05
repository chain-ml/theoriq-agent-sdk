from theoriq.schemas import ExecuteRequestBody


def test_schemas():
    request_body = {
        "items": [
            {
                "timestamp": "123",
                "sourceType": "user",
                "source": "0x012345689abcdef0123456789abcdef012345689abcdef0123456789abcdef01234567",
                "blocks": [
                    {
                        "data": {"items": [{"name": "route1", "score": 0.73}, {"name": "route2", "score": 0.27}]},
                        "type": "route",
                    },
                    {"data": {"text": "My name is John Doe"}, "type": "text"},
                ],
            }
        ]
    }

    req = ExecuteRequestBody.model_validate(request_body)
    assert req.items[0].blocks[0].data[0].name == "route1"
    assert req.items[0].blocks[0].data[1].score == 0.27
    assert req.items[0].blocks[1].data.text == "My name is John Doe"
