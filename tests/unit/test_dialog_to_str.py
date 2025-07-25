from theoriq.dialog import (
    CodeData,
    DataItem,
    ErrorData,
    MetricsData,
    RouterData,
    RouterItem,
    TextData,
    UnknownCommandData,
    Web3ProposedTxData,
    Web3SignedTxData,
)
from theoriq.dialog.custom_items import CustomData


def test_code_to_str():
    code_data = CodeData(code="print('Hello, world!')", language="python")
    str_repr = code_data.to_str()

    assert "```python" in str_repr
    assert "print('Hello, world!')" in str_repr


def test_custom_to_str():
    code_data = CustomData(data={"key": "value"}, custom_type="custom_type_example")
    str_repr = code_data.to_str()

    print(str_repr)


def test_data_to_str():
    data_data = DataItem(data="1,2,3", type="csv")
    str_repr = data_data.to_str()

    assert "```csv" in str_repr
    assert "1,2,3" in str_repr


def test_error_to_str():
    error_data = ErrorData(err="Error: Hello, world!", message="Error message")
    str_repr = error_data.to_str()

    assert "Error: Hello, world!" in str_repr
    assert "Error message" in str_repr


def test_metrics_to_str():
    metrics_data = MetricsData.from_metric(name="some_metric", value=3.14, trend_percentage=0.12)
    str_repr = metrics_data.to_str()

    assert "some_metric" in str_repr
    assert "3.14" in str_repr
    assert "0.12" in str_repr


def test_router_to_str():
    router_data = RouterData(items=[RouterItem(name="model_a", score=0.99, reason="It's a good model")])
    str_repr = router_data.to_str()

    assert "model_a" in str_repr
    assert "0.99" in str_repr
    assert "It's a good model" in str_repr


def test_text_to_str():
    text_data = TextData(text="Hello, world!", type="md")
    str_repr = text_data.to_str()

    assert "```md" in str_repr
    assert "Hello, world!" in str_repr


def test_unknown_command_to_str():
    unknown_command_data = UnknownCommandData(name="command_abc", arguments={"key": "value"})
    str_repr = unknown_command_data.to_str()

    assert "command_abc" in str_repr
    assert "key" in str_repr
    assert "value" in str_repr


def test_web3_proposed_tx_to_str():
    web3_proposed_tx_data = Web3ProposedTxData(
        abi={"test": "abi"},
        description="Test transaction",
        known_addresses={"test": "0x123"},
        tx_chain_id=1,
        tx_to="0x4567456745674567456745674567456745674567",
        tx_gas_limit=21000,
        tx_data="0x789",
        tx_nonce=0,
        tx_value=1000000000000000000,  # 1 ETH in wei
    )
    str_repr = web3_proposed_tx_data.to_str()

    assert "0x4567456745674567456745674567456745674567" in str_repr
    assert "Test transaction" in str_repr
    assert "21000" in str_repr
    assert "1000000000000000000" in str_repr


def test_web3_signed_tx_to_str():
    web3_signed_tx_data = Web3SignedTxData(
        chain_id=8453, tx_hash="0xa43da2004cf4131acc2bd14ef6fb68ff47752d0df9036b5b4a145b3b886bc75b", status=1
    )
    str_repr = web3_signed_tx_data.to_str()

    assert "0xa43da2004cf4131acc2bd14ef6fb68ff47752d0df9036b5b4a145b3b886bc75b" in str_repr
    assert "8453" in str_repr
