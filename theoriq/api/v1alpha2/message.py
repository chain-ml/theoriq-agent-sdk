from __future__ import annotations

import uuid
from typing import Optional, Sequence

from biscuit_auth import KeyPair, PrivateKey

from theoriq import AgentDeploymentConfiguration, ExecuteResponse
from theoriq.biscuit import AgentAddress, TheoriqBudget, TheoriqRequest
from theoriq.dialog import Dialog, DialogItem, ItemBlock

from .protocol.biscuit_provider import BiscuitProvider, BiscuitProviderFromPrivateKey
from .protocol.protocol_client import ProtocolClient
from .schemas.request import ExecuteRequestBody


class Messenger:
    def __init__(
        self, private_key: PrivateKey, biscuit_provider: BiscuitProvider, client: Optional[ProtocolClient] = None
    ) -> None:
        """
        Initialize a Messenger instance, that can handle direct communication with other agents.

        Args:
            private_key: Agent private key
            biscuit_provider: The biscuit provider to use for authentication
            client: Optional protocol client, will create one from environment if not provided
        """
        self._client = client or ProtocolClient.from_env()
        self._biscuit_provider = biscuit_provider
        self._private_key = private_key

        key_pair = KeyPair.from_private_key(self._private_key)
        self._address = AgentAddress.from_public_key(key_pair.public_key)

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

        execute_request_body = ExecuteRequestBody(
            dialog=Dialog(items=[DialogItem.new(source=str(self._address), blocks=blocks)])
        )
        body = execute_request_body.model_dump_json().encode("utf-8")
        theoriq_request = TheoriqRequest.from_body(body=body, from_addr=self._address, to_addr=to_addr)

        theoriq_biscuit = self._biscuit_provider.get_biscuit()
        theoriq_biscuit = theoriq_biscuit.attenuate_for_request(
            agent_pk=self._private_key, request_id=uuid.uuid4(), facts=[theoriq_request, budget]
        )
        response = self._client.post_request(request_biscuit=theoriq_biscuit, content=body, to_addr=to_addr)
        return ExecuteResponse.from_protocol_response({"dialog_item": response}, 200)

    @classmethod
    def from_agent(
        cls, private_key: PrivateKey, address: Optional[AgentAddress] = None, client: Optional[ProtocolClient] = None
    ) -> Messenger:
        """
        Create a Messenger from an agent's private key and address.

        Args:
            private_key: The agent's private key used for authentication
            address: Optional agent's address, will derive from a private key if not provided
            client: Optional protocol client, will create one from environment if not provided

        Returns:
            A new Messenger instance configured with the agent's credentials
        """
        protocol_client = client or ProtocolClient.from_env()
        biscuit_provider = BiscuitProviderFromPrivateKey(
            private_key=private_key, address=address, client=protocol_client
        )
        return cls(private_key=private_key, biscuit_provider=biscuit_provider, client=protocol_client)

    @classmethod
    def from_env(cls, env_prefix: str = "") -> Messenger:
        """
        Create a Messenger from an agent's private key from environment variable.

        Args:
            env_prefix: Optional prefix for environment variable

        Returns:
            A new Messenger instance configured with the agent's credentials
        """
        config = AgentDeploymentConfiguration.from_env(env_prefix=env_prefix)
        return cls.from_agent(private_key=config.private_key)
