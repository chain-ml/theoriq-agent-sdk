from typing import Dict

import pytest
from tests.integration.agent_registry import AgentRegistry, AgentType

from theoriq.api.v1alpha2 import AgentResponse
from theoriq.api.v1alpha2.manage import DeployedAgentManager
from theoriq.api.v1alpha2.schemas import AgentWeb3Transaction, AgentWeb3TransactionHash


@pytest.mark.order(1)
@pytest.mark.usefixtures("agent_flask_apps")
def test_registration_owner(
    agent_registry: AgentRegistry, agent_map: Dict[str, AgentResponse], user_manager: DeployedAgentManager
) -> None:
    owner_agent_data = agent_registry.get_first_agent_of_type(AgentType.OWNER)
    agent = user_manager.create_agent(owner_agent_data.spec.metadata, owner_agent_data.spec.configuration)
    agent_map[agent.system.id] = agent


@pytest.mark.order(2)
@pytest.mark.usefixtures("agent_flask_apps")
def test_post_web3_transaction_as_user(user_manager: DeployedAgentManager) -> None:
    with pytest.raises(ValueError, match="Only agent can submit a transaction; authorized as user"):
        user_manager.submit_web3_transaction(raw_transaction="0x0123456789abcdef", metadata={"abc": "xyz"})


@pytest.mark.order(3)
@pytest.mark.usefixtures("agent_flask_apps")
def test_post_web3_transaction(owner_manager: DeployedAgentManager) -> None:
    tx_hash = owner_manager.submit_web3_transaction(raw_transaction="0x0123456789abcdef", metadata={"abc": "xyz"})

    assert isinstance(tx_hash, AgentWeb3TransactionHash)
    assert isinstance(tx_hash.tx_hash, str)

    transaction = owner_manager.get_web3_transaction(tx_hash.tx_hash)

    assert isinstance(transaction, AgentWeb3Transaction)


@pytest.mark.order(4)
@pytest.mark.usefixtures("agent_flask_apps")
def test_get_web3_transactions_as_user(user_manager: DeployedAgentManager) -> None:
    transactions = user_manager.get_web3_transactions()
    assert len(transactions) > 1
    assert isinstance(transactions[0], AgentWeb3Transaction)


@pytest.mark.order(5)
@pytest.mark.usefixtures("agent_flask_apps")
def test_get_web3_transactions(owner_manager: DeployedAgentManager) -> None:
    transactions = owner_manager.get_web3_transactions()
    assert len(transactions) == 1
    assert isinstance(transactions[0], AgentWeb3Transaction)


@pytest.mark.order(-1)
@pytest.mark.usefixtures("agent_flask_apps")
def test_deletion_owner(agent_map: Dict[str, AgentResponse], user_manager: DeployedAgentManager) -> None:
    for agent in agent_map.values():  # should be the only one in the map
        user_manager.delete_agent(agent.system.id)
