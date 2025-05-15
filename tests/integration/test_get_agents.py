import os
from typing import Final

import dotenv

from theoriq.api.v1alpha2 import AgentResponse, ProtocolClient
from theoriq.api.v1alpha2.manage import AgentManager
from theoriq.api.v1alpha2.protocol.biscuit_provider import BiscuitProviderFromAPIKey
from theoriq.biscuit.utils import get_user_address_from_biscuit

dotenv.load_dotenv()
THEORIQ_API_KEY: Final[str] = os.environ["THEORIQ_API_KEY"]


def get_user_address_from_api_key(api_key: str) -> str:
    biscuit_provider = BiscuitProviderFromAPIKey(api_key=api_key, client=ProtocolClient.from_env())
    theoriq_biscuit = biscuit_provider.get_biscuit()
    return get_user_address_from_biscuit(theoriq_biscuit.biscuit)


def test_get_agents_with_client() -> None:
    client = ProtocolClient.from_env()
    agents = client.get_agents()
    assert len(agents) > 0  # require at least one minted agent

    for agent in agents:
        assert isinstance(agent, AgentResponse)


def test_get_agents_with_manager() -> None:
    manager = AgentManager.from_api_key(api_key=THEORIQ_API_KEY)
    user_address = get_user_address_from_api_key(THEORIQ_API_KEY)

    agents = manager.get_agents()
    assert len(agents) > 0

    for agent in agents:
        if agent.system.owner_address == user_address:
            agent_private = manager.get_agent(agent.system.id)
            assert agent_private.configuration.deployment
