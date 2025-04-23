from typing import Final, Sequence, Tuple
from uuid import uuid4

from theoriq.biscuit import AgentAddress
from theoriq.dialog import DataItemBlock, Dialog, DialogItem, ItemBlock, TextItemBlock
from theoriq.types import SourceType

USER_ADDRESS: Final[str] = "0x1F32Bc2B1Ace25D762E22888a71C7eC0799D379f"
RANDOM_AGENT_ADDRESS: Final[str] = str(AgentAddress.random())

dialog_payload = {
    "items": [
        {
            "sourceType": str(SourceType.User),
            "source": USER_ADDRESS,
            "timestamp": "2024-11-04T20:00:39Z",
            "blocks": [{"data": {"text": "Give me the trending tokens in the last 24 hours"}, "type": "text"}],
            "requestId": [uuid4()],
            "sse": [],
        },
        {
            "sourceType": str(SourceType.Agent),
            "source": RANDOM_AGENT_ADDRESS,
            "timestamp": "2024-11-27T00:57:29.725500Z",
            "blocks": [{"data": {"text": "The trending tokens in the last 24 hours are ...."}, "type": "text"}],
            "requestId": [],
            "dialogId": "7f105329-a491-4f6f-8882-67627acce6bb",
            "sse": [],
        },
    ]
}


def test_dialog_deserialization() -> None:
    d: Dialog = Dialog.model_validate(dialog_payload)
    assert isinstance(d, Dialog)
    assert d.items[0].source_type == SourceType.User
    assert (
        next(iter(d.items[0].find_blocks_of_type("text"))).data.text
        == "Give me the trending tokens in the last 24 hours"
    )


def test_format_source() -> None:
    d: Dialog = Dialog.model_validate(dialog_payload)

    assert d.items[0].format_source(with_address=False) == "User"
    assert d.items[0].format_source(with_address=True) == f"User ({USER_ADDRESS})"
    assert d.items[1].format_source(with_address=False) == "Agent"
    assert d.items[1].format_source(with_address=True) == f"Agent ({RANDOM_AGENT_ADDRESS})"


def test_format_blocks() -> None:
    def get_test_item(blocks: Sequence[ItemBlock]) -> DialogItem:
        return DialogItem.new(source=RANDOM_AGENT_ADDRESS, blocks=blocks)

    d: Dialog = Dialog(
        items=[
            get_test_item([TextItemBlock(text="Some text"), TextItemBlock(text="Some markdown", sub_type="md")]),
            get_test_item([TextItemBlock(text="Some text"), DataItemBlock(data="1,2,3", data_type="csv")]),
        ]
    )

    expected = d.items[0].format_blocks()
    assert expected == ["Some text", "```md\nSome markdown\n```"]

    expected = d.items[1].format_blocks()
    assert expected == ["Some text", "```csv\n1,2,3\n```"]

    expected = d.items[1].format_blocks(block_types_to_format=[TextItemBlock])
    assert expected == ["Some text"]


def test_map() -> None:
    def format_item(dialog_item: DialogItem, with_address: bool = False, source_prefix: str = "") -> Tuple[str, str]:
        source_str = dialog_item.format_source(with_address=with_address)
        blocks_str = "\n".join(dialog_item.format_blocks())
        return f"{source_prefix}{source_str}", blocks_str

    d: Dialog = Dialog.model_validate(dialog_payload)

    expected = d.map(format_item)
    assert expected == [
        ("User", "Give me the trending tokens in the last 24 hours"),
        ("Agent", "The trending tokens in the last 24 hours are ...."),
    ]

    # expected = d.map(format_item)
    # assert expected == [
    #     (f"User ({USER_ADDRESS})", "Give me the trending tokens in the last 24 hours"),
    #     (f"Agent ({RANDOM_AGENT_ADDRESS})", "The trending tokens in the last 24 hours are ...."),
    # ]

    # expected = d.map(format_item, with_address=False, source_prefix = "Test ")
    # assert expected == [
    #     (f"Test User", "Give me the trending tokens in the last 24 hours"),
    #     (f"Test Agent", "The trending tokens in the last 24 hours are ...."),
    # ]
