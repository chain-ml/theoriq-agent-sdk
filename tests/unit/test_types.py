import pytest

from theoriq.biscuit import AgentAddress
from theoriq.types import Currency, SourceType

valid_agent_address = [
    "0x48656c6c6f20776f726c642c2074686948656c6c6f20776f726c642c20746869",
    "0x12346c6c6f20776f726c642c2074686948656c6c6f20776f726c642c20746869",
    "0x148656c6c6f20776f726c642c207468692346c6c6f20776f726c642c20FFFFFF",
]

invalid_agent_address = [
    ("0x148656c6c6f20776f726c642c207468692346c6c6f20776f726c642c20FFFF", "address must be 32 bytes long"),
    ("0x148656c6c6f20776f726c642c207468692346c6c6f20776f726c642c20XXXXXX", "address must only contain hex digits"),
]

valid_user_addresses = ["0x1F32Bc2B1Ace25D762E22888a71C7eC0799D379f", "1F32Bc2B1Ace25D762E22888a71C7eC0799D379f"]

invalid_user_addresses = ["0x1F32Bc2B1Ace25D762E22888a71C7eC0799D379", "0x1F32Bc2B1Ace25D762E22888a71C7eC0799D379f6"]


@pytest.mark.parametrize("address", valid_agent_address)
def test_valid_agent_address(address):
    agent_address = AgentAddress(address)
    assert str(agent_address) == address


@pytest.mark.parametrize("address,error_message", invalid_agent_address)
def test_invalid_agent_address_raise_type_error(address, error_message):
    with pytest.raises(TypeError) as exception_info:
        AgentAddress(address)
    assert str(exception_info.value) == error_message + f": {address}"


@pytest.mark.parametrize("address", valid_user_addresses)
def test__from_address__with_valid_user_address(address):
    assert SourceType.from_address(address) == SourceType.User


@pytest.mark.parametrize("address", invalid_user_addresses)
def test__from_address__with_invalid_user_address__raise_value_error(address):
    with pytest.raises(ValueError) as exception_info:
        SourceType.from_address(address)
    assert str(exception_info.value) == f"'{address}' is not a valid address"


@pytest.mark.parametrize("address", valid_agent_address)
def test__from_address__with_valid_agent_address(address):
    assert SourceType.from_address(address) == SourceType.Agent


def test__from_address__with_invalid_agent_address__raise_value_error():
    address = invalid_agent_address[0][0]
    with pytest.raises(ValueError) as exception_info:
        SourceType.from_address(address)
    assert str(exception_info.value) == f"'{address}' is not a valid address"


@pytest.mark.parametrize(
    "value,currency",
    [
        ("USDC", Currency.USDC),
        ("usdc", Currency.USDC),
        ("USDT", Currency.USDT),
        ("usdt", Currency.USDT),
        ("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", Currency.USDC),
        ("0xdAC17F958D2ee523a2206206994597C13D831ec7", Currency.USDT),
    ],
)
def test__currency_ctor__with_valid_value__returns_currency(value, currency):
    assert Currency(value) == currency


@pytest.mark.parametrize("value", ["Toto", "0x12", ""])
def test__currency_ctor__with_invalid_value__raise_value_error(value):
    with pytest.raises(ValueError) as exception_info:
        Currency(value)
    assert str(exception_info.value) == f"'{value}' is not a valid Currency"
