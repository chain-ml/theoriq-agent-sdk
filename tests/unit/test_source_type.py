from theoriq.biscuit import AgentAddress
from theoriq.types import SourceType


def test_source_type():
    st = SourceType.from_address(AgentAddress.random().address)
    assert st.is_agent

    st = SourceType.from_address("0x1234512345123451234512345123451234512345")
    assert st.is_user
