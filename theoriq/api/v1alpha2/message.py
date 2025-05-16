from __future__ import annotations

import uuid
from typing import Optional, Sequence

from biscuit_auth import PrivateKey

from theoriq import ExecuteResponse
from theoriq.biscuit import AgentAddress, TheoriqBudget, TheoriqRequest
from theoriq.dialog import Dialog, DialogItem, ItemBlock

from ...biscuit.utils import get_user_address_from_biscuit
from ..common import RequestSenderBase
from .protocol.biscuit_provider import (
    BiscuitProvider,
    BiscuitProviderFactory,
    BiscuitProviderFromAPIKey,
    BiscuitProviderFromPrivateKey,
)
from .protocol.protocol_client import ProtocolClient
from .schemas.request import ExecuteRequestBody


class Messenger(RequestSenderBase):
    """Handles direct communications with other agents."""

    def __init__(self, biscuit_provider: BiscuitProvider, client: Optional[ProtocolClient] = None) -> None:
        self._client = client or ProtocolClient.from_env()
        self._biscuit_provider = biscuit_provider

        self._private_key: Optional[PrivateKey] = None
        self._address: str

        if isinstance(biscuit_provider, BiscuitProviderFromAPIKey):
            theoriq_biscuit = biscuit_provider.get_biscuit()
            self._address = get_user_address_from_biscuit(theoriq_biscuit.biscuit)
        elif isinstance(biscuit_provider, BiscuitProviderFromPrivateKey):
            self._private_key = biscuit_provider._key_pair.private_key
            self._address = str(AgentAddress.from_public_key(biscuit_provider._key_pair.public_key))
        else:
            raise RuntimeError("Unknown BiscuitProvider")

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

        dialog = Dialog(items=[DialogItem.new(source=self._address, blocks=blocks)])
        execute_request_body = ExecuteRequestBody(dialog=dialog)
        body = execute_request_body.model_dump_json().encode("utf-8")

        theoriq_request = TheoriqRequest.from_body(body=body, from_addr=self._address, to_addr=to_addr)
        theoriq_biscuit = self._biscuit_provider.get_biscuit()
        theoriq_biscuit = theoriq_biscuit.attenuate_for_request(
            agent_pk=self._private_key, request_id=uuid.uuid4(), facts=[theoriq_request, budget]
        )
        response = self._client.post_request(request_biscuit=theoriq_biscuit, content=body, to_addr=to_addr)
        return ExecuteResponse.from_protocol_response({"dialog_item": response}, 200)

    @classmethod
    def from_api_key(cls, api_key: str) -> Messenger:
        return Messenger(biscuit_provider=BiscuitProviderFactory.from_api_key(api_key=api_key))

    @classmethod
    def from_env(cls, env_prefix: str = "") -> Messenger:
        return Messenger(biscuit_provider=BiscuitProviderFactory.from_env(env_prefix=env_prefix))
