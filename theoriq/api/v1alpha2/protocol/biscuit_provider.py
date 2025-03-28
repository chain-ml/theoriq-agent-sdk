import abc
import time
from typing import Optional

from biscuit_auth import PrivateKey
from biscuit_auth.biscuit_auth import KeyPair, PublicKey

from theoriq.api.v1alpha2 import ProtocolClient
from theoriq.biscuit import AgentAddress, TheoriqBiscuit
from theoriq.biscuit.authentication_biscuit import AuthenticationFacts
from theoriq.extra.flask.common import public_key


class BiscuitProvider(abc.ABC):
    def __init__(self):
        self._biscuit: Optional[TheoriqBiscuit] = None
        self._renew_after: int = int(time.time())

    @abc.abstractmethod
    def _get_new_biscuit(self) -> TheoriqBiscuit:
        pass

    def get_biscuit(self) -> TheoriqBiscuit:
        if self._biscuit is None or time.time() > self._renew_after:
            (self._biscuit, expires_at) = self._get_new_biscuit()
            self._renew_after = expires_at - 300
        return self._biscuit


class BiscuitProviderFromPrivateKey(BiscuitProvider):
    def __init__(self, private_key: PrivateKey, address: AgentAddress, client: ProtocolClient) -> None:
        super().__init__()
        self._key_pair = KeyPair.from_private_key(private_key)
        self._address: AgentAddress = address
        self._client = client

    def _get_new_biscuit(self) -> (TheoriqBiscuit, int):
        facts = AuthenticationFacts(self._address, self._key_pair.private_key)
        authentication_biscuit = facts.to_authentication_biscuit()
        result = self._client.get_biscuit(authentication_biscuit, self._key_pair.public_key)
        biscuit = TheoriqBiscuit.from_token(token=result.biscuit, public_key=self._client.public_key)
        return biscuit, result.data.expires_at

