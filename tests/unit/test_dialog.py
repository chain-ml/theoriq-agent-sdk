import json
from typing import Final, Sequence, Tuple
from uuid import uuid4

from theoriq.biscuit import AgentAddress
from theoriq.dialog import BlockBase, CommandBlock, Dialog, DialogItem, TextBlock, format_source_and_blocks
from theoriq.dialog.items import CodeBlock, DataBlock, Web3ProposedTxBlock, Web3SignedTxBlock
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

dialog_web3_payload = {
    "items": [
        {
            "sourceType": str(SourceType.User),
            "source": USER_ADDRESS,
            "timestamp": "2025-06-25T13:24:35-04:00",
            "blocks": [{"data": {"text": "Send me an approval tx for 2 WETH in decimal"}, "type": "text"}],
        },
        {
            "sourceType": str(SourceType.Agent),
            "source": RANDOM_AGENT_ADDRESS,
            "timestamp": "2025-06-25T17:24:46.532032Z",
            "blocks": [
                {
                    "type": "web3:proposedTx",
                    "data": {
                        "abi": {
                            "constant": False,
                            "inputs": [
                                {"name": "_spender", "type": "address"},
                                {"name": "_value", "type": "uint256"},
                            ],
                            "name": "approve",
                            "outputs": [{"name": "", "type": "bool"}],
                            "payable": False,
                            "stateMutability": "nonpayable",
                            "type": "function",
                        },
                        "description": "Approve WETH 0x4200000000000000000000000000000000000006 for the Uniswap V3 Position Manager in the amount of 2 WETH",
                        "knownAddresses": {"0x4200000000000000000000000000000000000006": "WETH"},
                        "txChainId": 8453,
                        "txData": "0x095ea4b300000000000000000000000003a520b32c04bf3b2e37beb72e919cf827eb34f10000000000000000000000000000000000000000000000001ac26d694ec60000",
                        "txGasLimit": 29279,
                        "txNonce": 42,
                        "txTo": "0x4200000000000000000000000000000000000006",
                    },
                }
            ],
        },
        {
            "sourceType": str(SourceType.User),
            "source": USER_ADDRESS,
            "timestamp": "2025-06-25T13:25:14-04:00",
            "blocks": [
                {
                    "data": {"text": "transaction sent successfully"},
                    "type": "text:markdown",
                },
                {
                    "data": {"text": "another text block"},
                    "type": "text",
                },
                {
                    "type": "web3:signedTx",
                    "data": {
                        "txHash": "0x0159def724215e361a61db0b25118ad09cb63cf88ea69bb26c53289e44255gb4",
                        "chainId": 8453,
                    },
                },
            ],
        },
    ]
}

dialog_commands_payload = {
    "items": [
        {
            "sourceType": str(SourceType.User),
            "source": USER_ADDRESS,
            "timestamp": "2024-11-04T20:00:39Z",
            "blocks": [
                {
                    "data": {"name": "search", "arguments": {"query": "Trending tokens in the last 24 hours"}},
                    "type": "command",
                },
                {
                    "data": {"name": "summarize", "arguments": {"compression_ratio": 0.5}},
                    "type": "command",
                },
            ],
        },
        {
            "sourceType": str(SourceType.Agent),
            "source": RANDOM_AGENT_ADDRESS,
            "timestamp": "2024-11-27T00:57:29.725500Z",
            "blocks": [{"data": {"text": "The trending tokens in the last 24 hours are ...."}, "type": "text"}],
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


def test_web3_dialog() -> None:
    d: Dialog = Dialog.model_validate(dialog_web3_payload)
    assert isinstance(d, Dialog)
    assert isinstance(d.items[1].blocks[0], Web3ProposedTxBlock)
    assert isinstance(d.items[2].blocks[-1], Web3SignedTxBlock)


def test_find_blocks_of_type() -> None:
    dialog: Dialog = Dialog.model_validate(dialog_web3_payload)

    agent_item, user_item = dialog.items[1], dialog.items[2]

    assert agent_item.has_blocks_of_type("text") == False
    assert not agent_item.has_blocks_of_type("text:markdown")
    assert not agent_item.has_blocks_of_type("text:unknown_subtype")
    assert agent_item.has_blocks_of_type("web3:proposedTx")
    assert len(agent_item.find_all_blocks_of_type("web3:proposedTx")) == 1
    assert not agent_item.has_blocks_of_type("web3:unknown_subtype")

    assert len(user_item.find_all_blocks_of_type("text")) == 2
    assert len(user_item.find_all_blocks_of_type("text:markdown")) == 1
    assert not agent_item.has_blocks_of_type("text:unknown_subtype")
    assert len(user_item.find_all_blocks_of_type("web3:signedTx")) == 1
    assert not agent_item.has_blocks_of_type("web3:unknown_subtype")

    first_web3_block = user_item.find_first_block_of_type("web3:signedTx")
    last_web3_block = user_item.find_last_block_of_type("web3:signedTx")
    assert first_web3_block == last_web3_block

    first_text_block = user_item.find_first_block_of_type("text")
    last_text_block = user_item.find_last_block_of_type("text")
    assert isinstance(first_text_block, TextBlock) and isinstance(last_text_block, TextBlock)
    assert first_text_block.data.text == "transaction sent successfully"
    assert last_text_block.data.text == "another text block"

    assert user_item.find_first_block_of_type("unknown_type") is None


def test_commands_dialog() -> None:
    d: Dialog = Dialog.model_validate(dialog_commands_payload)
    search_command_block, summarize_command_block = d.items[0].blocks[0], d.items[0].blocks[1]

    assert isinstance(search_command_block, CommandBlock)
    assert isinstance(summarize_command_block, CommandBlock)

    assert search_command_block.data.name == "search"
    assert search_command_block.data.arguments == {"query": "Trending tokens in the last 24 hours"}

    assert summarize_command_block.data.name == "summarize"
    assert summarize_command_block.data.arguments == {"compression_ratio": 0.5}


def test_format_source() -> None:
    d: Dialog = Dialog.model_validate(dialog_payload)

    assert d.items[0].format_source(with_address=False) == "User"
    assert d.items[0].format_source(with_address=True) == f"User ({USER_ADDRESS})"
    assert d.items[1].format_source(with_address=False) == "Agent"
    assert d.items[1].format_source(with_address=True) == f"Agent ({RANDOM_AGENT_ADDRESS})"


def test_format_blocks() -> None:
    def get_test_item(blocks: Sequence[BlockBase]) -> DialogItem:
        return DialogItem.new(source=RANDOM_AGENT_ADDRESS, blocks=blocks)

    d: Dialog = Dialog(
        items=[
            get_test_item(
                [TextBlock.from_text(text="Some text"), TextBlock.from_text(text="Some markdown", sub_type="md")]
            ),
            get_test_item(
                [
                    TextBlock.from_text(text="Another text"),
                    CodeBlock.from_code(code="SELECT *"),
                    DataBlock.from_data(data="1,2,3", sub_type="csv"),
                ]
            ),
        ]
    )

    expected = d.items[0].format_blocks()
    assert expected == ["Some text", "```md\nSome markdown\n```"]

    expected = d.items[1].format_blocks()
    assert expected == ["Another text", "```\nSELECT *\n```", "```csv\n1,2,3\n```"]

    expected = d.items[1].format_blocks(block_types_to_format=[TextBlock, CodeBlock])
    assert expected == ["Another text", "```\nSELECT *\n```"]


def test_map_format_source_and_blocks() -> None:
    d: Dialog = Dialog.model_validate(dialog_payload)

    expected = d.map(format_source_and_blocks)
    assert expected == [
        (f"User ({USER_ADDRESS})", "Give me the trending tokens in the last 24 hours"),
        (f"Agent ({RANDOM_AGENT_ADDRESS})", "The trending tokens in the last 24 hours are ...."),
    ]

    def format_source_and_blocks_without_address(item: DialogItem) -> Tuple[str, str]:
        return format_source_and_blocks(item, with_address=False)

    expected = d.map(format_source_and_blocks_without_address)
    assert expected == [
        ("User", "Give me the trending tokens in the last 24 hours"),
        ("Agent", "The trending tokens in the last 24 hours are ...."),
    ]

    def format_source_and_blocks_without_address_with_prefix(item: DialogItem) -> Tuple[str, str]:
        source_str, blocks_str = format_source_and_blocks(item, with_address=False)
        return f"Test {source_str}", blocks_str

    expected = d.map(format_source_and_blocks_without_address_with_prefix)
    assert expected == [
        ("Test User", "Give me the trending tokens in the last 24 hours"),
        ("Test Agent", "The trending tokens in the last 24 hours are ...."),
    ]


def test_format_md() -> None:
    d: Dialog = Dialog.model_validate(dialog_payload)

    expected = d.format_as_markdown(indent=3)
    assert expected == "\n".join(
        [
            f"### User ({USER_ADDRESS})",
            "",
            "Give me the trending tokens in the last 24 hours",
            "",
            f"### Agent ({RANDOM_AGENT_ADDRESS})",
            "",
            "The trending tokens in the last 24 hours are ....",
        ]
    )


def test_dialog() -> None:
    for dialog in [dialog_payload, dialog_commands_payload, dialog_web3_payload]:
        dialog = Dialog.model_validate(dialog)
        print(dialog.model_dump_json(indent=2))


def test_dialog_schema() -> None:
    print(json.dumps(TextBlock.model_json_schema(), indent=2))


def test_dialog_v2_text_item() -> None:
    # item = dialogv2.TextBlock(type="text", data=dialogv2.TextData(text="some text"), key=None)
    item = TextBlock.from_text("some text")
    print(item.model_dump_json(indent=2))
