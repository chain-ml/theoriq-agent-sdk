from theoriq.dialog import (
    CodeData,
    DataItem,
    ErrorData,
    MetricsData,
    RouterData,
    RouterItem,
    TextData,
    Web3ProposedTxData,
    Web3SignedTxData,
)
from theoriq.dialog.commands import UnknownCommandData


def test_text_to_str():
    text_data = TextData(text="Hello, world!", type="md")
    str_repr = text_data.to_str()
    print(str_repr)
    assert isinstance(str_repr, str)


def test_code_to_str():
    code_data = CodeData(code="print('Hello, world!')", language="python")
    str_repr = code_data.to_str()
    print(str_repr)
    assert isinstance(str_repr, str)


def test_data_to_str():
    data_data = DataItem(data="1,2,3", type="csv")
    str_repr = data_data.to_str()
    print(str_repr)
    assert isinstance(str_repr, str)


def test_error_to_str():
    error_data = ErrorData(err="Error: Hello, world!", message="Error message")
    str_repr = error_data.to_str()
    print(str_repr)
    assert isinstance(str_repr, str)


def test_metrics_to_str():
    metrics_data = MetricsData.from_metric(name="metric", value=3.14, trend_percentage=0.12)
    str_repr = metrics_data.to_str()
    print(str_repr)
    assert isinstance(str_repr, str)


def test_router_to_str():
    router_data = RouterData(items=[RouterItem(name="model_a", score=0.99, reason="It's a good model")])
    str_repr = router_data.to_str()
    print(str_repr)
    assert isinstance(str_repr, str)


def test_unknown_command_to_str():
    unknown_command_data = UnknownCommandData(name="command", arguments={"key": "value"})
    str_repr = unknown_command_data.to_str()
    print(str_repr)
    assert isinstance(str_repr, str)


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
    )
    str_repr = web3_proposed_tx_data.to_str()
    print(str_repr)
    assert isinstance(str_repr, str)


def test_web3_signed_tx_to_str():
    web3_signed_tx_data = Web3SignedTxData(
        chain_id=1, tx_hash="0xa43da2004cf4131acc2bd14ef6fb68ff47752d0df9036b5b4a145b3b886bc75b", status=1
    )
    str_repr = web3_signed_tx_data.to_str()
    print(str_repr)
