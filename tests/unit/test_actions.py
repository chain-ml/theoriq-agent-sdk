from typing import Final, Sequence

from theoriq.biscuit import AgentAddress
from theoriq.dialog import ActionItem, ActionsItemBlock, Dialog, DialogItem
from theoriq.types import SourceType

USER_ADDRESS: Final[str] = "0x1F32Bc2B1Ace25D762E22888a71C7eC0799D379f"
RANDOM_AGENT_ADDRESS: Final[str] = str(AgentAddress.random())


dialog_actions_payload = {
    "items": [
        {
            "sourceType": str(SourceType.User),
            "source": USER_ADDRESS,
            "timestamp": "2025-06-30T12:00:00Z",
            "blocks": [
                {"data": {"text": "Choose an option"}, "type": "text"},
            ],
        },
        {
            "sourceType": str(SourceType.Agent),
            "source": RANDOM_AGENT_ADDRESS,
            "timestamp": "2025-06-30T12:00:02Z",
            "blocks": [
                {
                    "type": "actions",
                    "key": "proposal-1",
                    "data": {
                        "items": [
                            {"id": "approve", "label": "Approve", "description": "Approve transfer"},
                            {"id": "reject", "label": "Reject"},
                        ]
                    },
                }
            ],
        },
    ]
}


def test_actions_block_deserialization_roundtrip() -> None:
    """The payload should parse into Dialog and then round-trip back unchanged."""
    d: Dialog = Dialog.model_validate(dialog_actions_payload)

    # Agent message should contain an ActionsItemBlock
    assert isinstance(d.items[1].blocks[0], ActionsItemBlock)
    block: ActionsItemBlock = d.items[1].blocks[0]  # type: ignore[assignment]

    # First action should be the approve button
    assert block.data[0].id == "approve"
    assert block.data[0].label == "Approve"

    # Round-trip: model_dump() then validate again should produce equivalent structure
    dumped = d.model_dump(mode="python")
    reparsed = Dialog.model_validate(dumped).model_dump(mode="python")
    assert dumped == reparsed


def test_new_actions_helper() -> None:
    """`DialogItem.new_actions` should create a correct Actions block."""
    actions: Sequence[ActionItem] = [
        ActionItem(id="yes", label="Yes"),
        ActionItem(id="no", label="No"),
    ]
    item: DialogItem = DialogItem.new_actions(source=RANDOM_AGENT_ADDRESS, actions=actions, key="q1")

    assert isinstance(item.blocks[0], ActionsItemBlock)
    block: ActionsItemBlock = item.blocks[0]  # type: ignore[assignment]
    assert len(block.data) == 2
    assert block.find("yes") is not None
