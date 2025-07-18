from __future__ import annotations

import abc
from typing import Any, Dict, Optional, Sequence

from ..biscuit import RequestBiscuit, ResponseBiscuit
from ..dialog import DialogItem, BlockBase, TextBlock
from ..types import AgentMetadata, SourceType
from ..utils import TTLCache
from .v1alpha2.agent import Agent


class RequestSenderBase(abc.ABC):
    @abc.abstractmethod
    def send_request(self, blocks: Sequence[BlockBase], to_addr: str) -> ExecuteResponse:
        """
        Sends a request to another address, attenuating the biscuit for the request and handling the response.

        Args:
            blocks (Sequence[ItemBlock]): The blocks of data to include in the request.
            to_addr (str): The address to which the request is sent.

        Returns:
            ExecuteResponse: The response received from the request.
        """
        pass

    def send_text_request(self, *, message: str, to_addr: str) -> ExecuteResponse:
        return self.send_request(blocks=[TextBlock.from_text(message)], to_addr=to_addr)


class ExecuteContextBase(RequestSenderBase):
    """
    Represents the context for executing a request, managing interactions with the agent and protocol client.
    """

    _metadata_cache: TTLCache[AgentMetadata] = TTLCache(ttl=180, max_size=40)

    def __init__(self, agent: Agent, request_biscuit: RequestBiscuit) -> None:
        """
        Initializes an ExecuteContext instance.

        Args:
            agent (Agent): The agent responsible for handling the execution.
            request_biscuit (RequestBiscuit): The biscuit associated with the request, containing metadata and permissions.
        """
        self._agent = agent
        self._request_biscuit = request_biscuit

    def new_response_biscuit(self, body: bytes) -> ResponseBiscuit:
        """
        Builds a biscuit for the response to an 'execute' request.

        Args:
            body (bytes): The body content of the response.

        Returns:
            ResponseBiscuit: A biscuit for the response, incorporating the provided body.
        """
        return self._agent.attenuate_biscuit_for_response(self._request_biscuit, body)

    def new_error_response_biscuit(self, body: bytes) -> ResponseBiscuit:
        """
        Builds a biscuit for the response to an 'execute' request in case of an error.

        Args:
            body (bytes): The body content of the error response.

        Returns:
            ResponseBiscuit: A biscuit for the error response.
        """
        return self._agent.attenuate_biscuit_for_response(self._request_biscuit, body)

    def new_text_response(self, text: str) -> ExecuteResponse:
        """
        Creates a new response containing single TextItemBlock.

        Args:
            text (str): Text to include in the response.

        Returns:
            ExecuteResponse: The response object with single TextItemBlock.
        """
        return self.new_response(blocks=[TextBlock.from_text(text=text)])

    def new_response(self, blocks: Sequence[BlockBase]) -> ExecuteResponse:
        """
        Creates a new response with the specified blocks.

        Args:
            blocks (Sequence[ItemBlock]): The blocks of data to include in the response.

        Returns:
            ExecuteResponse: The response object with the provided blocks.
        """
        return ExecuteResponse(dialog_item=DialogItem.new(source=self.agent_address, blocks=blocks))

    def runtime_error_response(self, err: ExecuteRuntimeError) -> ExecuteResponse:
        """
        Creates a response for a runtime error.

        Args:
            err (ExecuteRuntimeError): The runtime error to respond to.

        Returns:
            ExecuteResponse: The response object encapsulating the error.
        """
        return self.new_response(blocks=[ErrorBlock.new(err=err.err, message=err.message)])

    @property
    def agent_address(self) -> str:
        """
        Returns the address of the agent.
        If the agent is virtual return the virtual address

        Returns:
            str: The agent's address as a string.
        """
        if self._agent.virtual_address.is_null:
            return str(self._agent.config.address)
        return str(self._agent.virtual_address)

    @property
    def request_id(self) -> str:
        """
        Returns the request ID from the request biscuit.

        Returns:
            str: The request ID as a string.
        """
        return str(self._request_biscuit.request_facts.req_id)

    @property
    def request_sender_type(self) -> SourceType:
        """
        Returns the source type of the sender or the request from the request biscuit.

        Returns:
            SourceType: The source type of the sender of the request.
        """

        return SourceType.from_address(self._request_biscuit.request_facts.request.from_addr)

    @property
    def request_sender_address(self) -> str:
        """
        Returns the address of the sender of the request from the request biscuit.

        Returns:
            str: The address of the sender of the request as a string.
        """
        return self._request_biscuit.request_facts.request.from_addr

    @property
    def sender_kind(self) -> SourceType:
        return SourceType.from_address(self._request_biscuit.request_facts.request.from_addr)

    @property
    def sender_metadata(self) -> Optional[AgentMetadata]:
        if self.sender_kind.is_user:
            return None

        key = self._request_biscuit.request_facts.request.from_addr
        result = self._metadata_cache.get(key)
        if result is not None:
            return result

        result = self._sender_metadata(key)
        self._metadata_cache.set(key, result)
        return result

    @abc.abstractmethod
    def _sender_metadata(self, agent_id: str) -> AgentMetadata:
        pass


class ExecuteResponse:
    """
    Represents the result of executing a theoriq request.

    Attributes:
        body (DialogItem): The dialog item to encapsulate in the response payload.
        status_code (int, optional): The status code of the response. Defaults to 200.
    """

    def __init__(self, dialog_item: DialogItem, status_code: int = 200) -> None:
        """
        Initializes an ExecuteResponse instance.

        Args:
            dialog_item (DialogItem): The dialog item to be included in the response body.
            status_code (int, optional): The HTTP status code for the response. Defaults to 200.
        """
        self.body = dialog_item
        self.status_code = status_code

    def __str__(self) -> str:
        """
        Returns a string representation of the ExecuteResponse instance.

        Returns:
            str: A string representing the ExecuteResponse, including the body and status code.
        """
        return f"ExecuteResponse(body={self.body}, status_code={self.status_code})"

    @classmethod
    def from_protocol_response(cls, data: Dict[str, Any], status_code: int) -> ExecuteResponse:
        """
        Creates an instance of ExecuteResponse from a protocol response.

        Args:
            data (Dict[str, Any]): The dictionary containing the dialog item data.
            status_code (int): The HTTP status code for the response.

        Returns:
            ExecuteResponse: A new instance of ExecuteResponse initialized with the provided data.
        """
        # Convert the dialog item from the dictionary format.
        dialog_item = DialogItem.model_validate(data["dialog_item"])
        return cls(
            dialog_item=dialog_item,
            status_code=status_code,
        )


class ExecuteRuntimeError(RuntimeError):
    """
    Custom exception class for runtime errors during the execution of a request.

    Attributes:
        err (str): The error code or message.
        message (Optional[str]): An optional message providing additional context for the error.
    """

    def __init__(self, err: str, message: Optional[str] = None) -> None:
        """
        Initializes an ExecuteRuntimeError instance.

        Args:
            err (str): The error code or message.
            message (Optional[str]): An optional additional message providing more details about the error.
        """
        # Calls the base class constructor with a combined error and message if both are provided.
        super().__init__(err if message is None else f"{err}, {message}")
        self.err = err
        self.message = message
