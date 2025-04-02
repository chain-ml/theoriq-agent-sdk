import abc
import time
from typing import Optional, Tuple

from biscuit_auth import PrivateKey
from biscuit_auth.biscuit_auth import KeyPair

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
