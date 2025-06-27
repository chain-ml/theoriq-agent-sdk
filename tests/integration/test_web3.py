from typing import Dict, Final

import httpx
import pytest
from tests.integration.agent_registry import AgentRegistry, AgentType

from theoriq.api.v1alpha2 import AgentResponse
from theoriq.api.v1alpha2.manage import DeployedAgentManager
from theoriq.api.v1alpha2.schemas import AgentWeb3Transaction

ETH_SEPOLIA_TX_HASH: Final[str] = "0xa8f64019914a952349d168340b5e7051c72bd722e60346defeb48bf99f5fdad1"
ETH_SEPOLIA_CHAIN_ID: Final[int] = 11155111
METADATA: Final[Dict[str, str]] = {"abc": "xyz"}


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
    with pytest.raises(httpx.HTTPStatusError) as e:
        user_manager.post_web3_transaction(ETH_SEPOLIA_TX_HASH, ETH_SEPOLIA_CHAIN_ID)
    assert e.value.response.status_code == 401


@pytest.mark.order(3)
@pytest.mark.usefixtures("agent_flask_apps")
def test_post_web3_transaction(owner_manager: DeployedAgentManager) -> None:
    owner_manager.post_web3_transaction(tx_hash=ETH_SEPOLIA_TX_HASH, chain_id=ETH_SEPOLIA_CHAIN_ID, metadata=METADATA)


@pytest.mark.order(4)
@pytest.mark.usefixtures("agent_flask_apps")
def test_get_web3_transaction(owner_manager: DeployedAgentManager) -> None:
    tx = owner_manager.get_web3_transaction(ETH_SEPOLIA_TX_HASH)

    assert isinstance(tx, AgentWeb3Transaction)
    assert tx.chain_id == ETH_SEPOLIA_CHAIN_ID
    assert tx.hash == ETH_SEPOLIA_TX_HASH
    assert tx.metadata == METADATA


@pytest.mark.order(5)
@pytest.mark.usefixtures("agent_flask_apps")
def test_get_web3_transactions_as_user(user_manager: DeployedAgentManager) -> None:
    transactions = user_manager.get_web3_transactions()

    assert len(transactions) >= 1
    assert isinstance(transactions[0], AgentWeb3Transaction)


@pytest.mark.order(6)
@pytest.mark.usefixtures("agent_flask_apps")
def test_get_web3_transactions(owner_manager: DeployedAgentManager) -> None:
    transactions = owner_manager.get_web3_transactions()

    assert len(transactions) >= 1
    assert isinstance(transactions[0], AgentWeb3Transaction)


@pytest.mark.order(-1)
@pytest.mark.usefixtures("agent_flask_apps")
def test_deletion_owner(agent_map: Dict[str, AgentResponse], user_manager: DeployedAgentManager) -> None:
    for agent in agent_map.values():
        user_manager.delete_agent(agent.system.id)
