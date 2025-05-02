from __future__ import annotations

import uuid
from typing import Optional, Sequence

from biscuit_auth import KeyPair, PrivateKey

from theoriq import AgentDeploymentConfiguration, ExecuteResponse
from theoriq.biscuit import AgentAddress, TheoriqBudget, TheoriqRequest
from theoriq.dialog import Dialog, DialogItem, ItemBlock

from ...biscuit.utils import get_user_address_from_biscuit
from ..common import RequestSenderBase
from .protocol.biscuit_provider import BiscuitProvider, BiscuitProviderFactory, BiscuitProviderFromAPIKey
from .protocol.protocol_client import ProtocolClient
from .schemas.request import ExecuteRequestBody


class Messenger(RequestSenderBase):
    def __init__(
        self, private_key: PrivateKey, biscuit_provider: BiscuitProvider, client: Optional[ProtocolClient] = None
    ) -> None:
        # note: for user (e.g. BiscuitProviderFromAPIKey) pass any private key as a placeholder
        # implementation should use different attenuate function
        self._client = client or ProtocolClient.from_env()
        self._biscuit_provider = biscuit_provider
        self._private_key = private_key

        key_pair = KeyPair.from_private_key(self._private_key)
        self._agent_address = AgentAddress.from_public_key(key_pair.public_key)

        self._user_address: Optional[str] = None
        if isinstance(biscuit_provider, BiscuitProviderFromAPIKey):
            theoriq_biscuit = biscuit_provider.get_biscuit()
            self._user_address = get_user_address_from_biscuit(theoriq_biscuit.biscuit)

    def send_request(self, blocks: Sequence[ItemBlock], budget: TheoriqBudget, to_addr: str) -> ExecuteResponse:
        """
        Sends a request to another address, attenuating the biscuit for the request and handling the response.

        Args:
            blocks (Sequence[ItemBlock]): The blocks of data to include in the request.
            budget (TheoriqBudget): The budget for processing the request.
            to_addr (str): The address to which the request is sent.

        Returns:
            ExecuteResponse: The response received from the request.
        """
        address: str = str(self._user_address or self._agent_address)

        execute_request_body = ExecuteRequestBody(dialog=Dialog(items=[DialogItem.new(source=address, blocks=blocks)]))
        body = execute_request_body.model_dump_json().encode("utf-8")

        # 0x prefix required for users only; must be omitted for agents
        from_addr = self._user_address if self._user_address is not None else self._agent_address

        theoriq_request = TheoriqRequest.from_body(body=body, from_addr=from_addr, to_addr=to_addr)
        theoriq_biscuit = self._biscuit_provider.get_biscuit()
        theoriq_biscuit = theoriq_biscuit.attenuate_for_request(
            agent_pk=self._private_key, request_id=uuid.uuid4(), facts=[theoriq_request, budget]
        )
        response = self._client.post_request(request_biscuit=theoriq_biscuit, content=body, to_addr=to_addr)
        return ExecuteResponse.from_protocol_response({"dialog_item": response}, 200)

    @classmethod
    def from_api_key(cls, api_key: str) -> Messenger:
        return Messenger(
            # generating new private key as a placeholder, should use different attenuate function
            private_key=KeyPair().private_key,
            biscuit_provider=BiscuitProviderFactory.from_api_key(api_key=api_key),
        )

    @classmethod
    def from_env(cls, env_prefix: str = "") -> Messenger:
        config = AgentDeploymentConfiguration.from_env(env_prefix=env_prefix)
        biscuit_provider = BiscuitProviderFactory.from_env(env_prefix=env_prefix)
        return Messenger(private_key=config.private_key, biscuit_provider=biscuit_provider)
