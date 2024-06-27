import pytest

from theoriq.types import AgentAddress


valid_agent_address = [
    "48656c6c6f20776f726c642c2074686948656c6c6f20776f726c642c20746869",
    "12346c6c6f20776f726c642c2074686948656c6c6f20776f726c642c20746869",
    "148656c6c6f20776f726c642c207468692346c6c6f20776f726c642c20FFFFFF",
]

invalid_agent_address = [
    ("148656c6c6f20776f726c642c207468692346c6c6f20776f726c642c20FFFF", "address must be 32 bytes long"),
    ("148656c6c6f20776f726c642c207468692346c6c6f20776f726c642c20XXXXXX", "address must only contain hex digits"),
]


@pytest.mark.parametrize("address", valid_agent_address)
def test_valid_agent_address(address):
    agent_address = AgentAddress(address)
    assert str(agent_address) == address


@pytest.mark.parametrize("address,error_message", invalid_agent_address)
def test_invalid_agent_address_raise_type_error(address, error_message):
    with pytest.raises(TypeError) as exception_info:
        AgentAddress(address)
    assert str(exception_info.value) == error_message + f": {address}"
