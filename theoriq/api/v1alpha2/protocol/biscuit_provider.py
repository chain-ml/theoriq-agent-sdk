import abc
import time
from typing import Optional, Tuple

from biscuit_auth import PrivateKey
from biscuit_auth.biscuit_auth import KeyPair

from theoriq import AgentDeploymentConfiguration
from theoriq.api.v1alpha2 import ProtocolClient
from theoriq.biscuit import AgentAddress, TheoriqBiscuit
from theoriq.biscuit.authentication_biscuit import AuthenticationBiscuit, AuthenticationFacts
from theoriq.biscuit.facts import ExpiresAtFact


class BiscuitProvider(abc.ABC):
    def __init__(self) -> None:
        self._biscuit: Optional[TheoriqBiscuit] = None
        self._renew_after: int = int(time.time())

    @abc.abstractmethod
    def _get_new_biscuit(self) -> Tuple[TheoriqBiscuit, int]:
        pass

    def get_biscuit(self) -> TheoriqBiscuit:
        if self._biscuit is None or time.time() > self._renew_after:
            (self._biscuit, expires_at) = self._get_new_biscuit()
            self._renew_after = expires_at - 300
        return self._biscuit


class BiscuitProviderFromPrivateKey(BiscuitProvider):
    def __init__(self, private_key: PrivateKey, address: Optional[AgentAddress], client: ProtocolClient) -> None:
        super().__init__()
        self._key_pair = KeyPair.from_private_key(private_key)
        self._address: AgentAddress = address or AgentAddress.from_public_key(self._key_pair.public_key)
        self._client = client

    def _get_new_biscuit(self) -> Tuple[TheoriqBiscuit, int]:
        facts = AuthenticationFacts(self._address, self._key_pair.private_key)
        authentication_biscuit = facts.to_authentication_biscuit()
        result = self._client.get_biscuit(authentication_biscuit, self._key_pair.public_key)
        biscuit = TheoriqBiscuit.from_token(token=result.biscuit, public_key=self._client.public_key)
        return biscuit, result.data.expires_at


class BiscuitProviderFromAPIKey(BiscuitProvider):
    def __init__(self, api_key: str, client: ProtocolClient) -> None:
        super().__init__()
        self._api_key_biscuit = TheoriqBiscuit.from_token(token=api_key, public_key=client.public_key)
        self._client = client

    def _get_new_biscuit(self) -> Tuple[TheoriqBiscuit, int]:
        new_biscuit = self._api_key_biscuit.attenuate(ExpiresAtFact.from_lifetime_duration(300))
        result = self._client.api_key_exchange(AuthenticationBiscuit(new_biscuit.biscuit))
        biscuit = TheoriqBiscuit.from_token(token=result.biscuit, public_key=self._client.public_key)
        return biscuit, result.data.expires_at


class BiscuitProviderFactory:
    @staticmethod
    def from_api_key(api_key: str, client: Optional[ProtocolClient] = None) -> BiscuitProviderFromAPIKey:
        """
        Create a BiscuitProvider from an API key.

        Args:
            api_key: The API key used for authentication
            client: Optional protocol client, will create one from environment if not provided

        Returns:
            A BiscuitProvider instance configured with the API key
        """
        protocol_client = client or ProtocolClient.from_env()
        return BiscuitProviderFromAPIKey(api_key=api_key, client=protocol_client)

    @staticmethod
    def from_agent(
        private_key: PrivateKey, address: Optional[AgentAddress] = None, client: Optional[ProtocolClient] = None
    ) -> BiscuitProviderFromPrivateKey:
        """
        Create a BiscuitProvider from an agent's private key and address.

        Args:
            private_key: The agent's private key used for authentication
            address: Optional agent's address, will derive from a private key if not provided
            client: Optional protocol client, will create one from environment if not provided

        Returns:
            A BiscuitProvider instance configured with the agent's credentials
        """
        protocol_client = client or ProtocolClient.from_env()
        return BiscuitProviderFromPrivateKey(private_key=private_key, address=address, client=protocol_client)

    @staticmethod
    def from_env(env_prefix: str = "", client: Optional[ProtocolClient] = None) -> BiscuitProviderFromPrivateKey:
        """
        Create a BiscuitProvider from an agent's private key environment variable.

        Args:
            env_prefix: Optional prefix for environment variable
            client: Optional protocol client, will create one from environment if not provided

        Returns:
            A BiscuitProvider instance configured with the agent's credentials from environment
        """
        config = AgentDeploymentConfiguration.from_env(env_prefix=env_prefix)
        return BiscuitProviderFactory.from_agent(private_key=config.private_key, client=client)
