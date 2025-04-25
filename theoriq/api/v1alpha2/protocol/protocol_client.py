from __future__ import annotations

import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Final, Iterator, List, Optional, Sequence
from uuid import UUID

import httpx
from biscuit_auth import PublicKey
from pydantic import BaseModel

from theoriq import Agent
from theoriq.biscuit import AgentAddress, PayloadHash, RequestBiscuit, RequestFact, ResponseFact, TheoriqBiscuit
from theoriq.biscuit.authentication_biscuit import AuthenticationBiscuit
from theoriq.types import Metric
from theoriq.utils import TTLCache, is_protocol_secured

from ..schemas.agent import AgentResponse
from ..schemas.api import PublicKeyResponse
from ..schemas.biscuit import BiscuitResponse
from ..schemas.event_request import EventRequestBody
from ..schemas.metrics import MetricsRequestBody


class ConfigureResponse(BaseModel):
    response: Any


class RequestStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"


class ProtocolClient:
    _config_cache: TTLCache[Dict[str, Any]] = TTLCache()
    _public_key_cache: TTLCache[PublicKeyResponse] = TTLCache(ttl=None, max_size=5)

    def __init__(self, uri: str, timeout: Optional[int] = 120, max_retries: Optional[int] = None) -> None:
        self._uri = f"{uri}/api/v1alpha2"
        self._timeout = timeout
        self._max_retries = max_retries or 0

    @property
    def public_key(self) -> str:
        key = self._public_key_cache.get(self._uri)
        if key is None:
            key = self.get_public_key()
            self._public_key_cache.set(self._uri, key)
        return key.public_key

    def get_public_key(self) -> PublicKeyResponse:
        with httpx.Client(timeout=self._timeout) as client:
            response = client.get(url=f"{self._uri}/auth/biscuits/public-key")
            response.raise_for_status()
            data = response.json()
            return PublicKeyResponse(**data)

    def get_biscuit(self, authentication_biscuit: AuthenticationBiscuit, public_key: PublicKey) -> BiscuitResponse:
        url = f"{self._uri}/auth/biscuits/biscuit"
        headers = authentication_biscuit.to_headers()
        body = {"publicKey": public_key.to_hex()}
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(url=url, json=body, headers=headers)
            response.raise_for_status()
            return BiscuitResponse.model_validate(response.json())

    def api_key_exchange(self, api_key_biscuit: AuthenticationBiscuit) -> BiscuitResponse:
        url = f"{self._uri}/auth/api-keys/exchange"
        headers = api_key_biscuit.to_headers()
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(url=url, headers=headers)
            response.raise_for_status()
            return BiscuitResponse.model_validate(response.json())

    def get_agent(self, agent_id: str) -> AgentResponse:
        with httpx.Client(timeout=self._timeout) as client:
            response = client.get(url=f'{self._uri}/agents/0x{agent_id.removeprefix("0x")}')
            response.raise_for_status()
            return AgentResponse.model_validate(response.json())

    def get_agents(self) -> List[AgentResponse]:
        with httpx.Client(timeout=self._timeout) as client:
            response = client.get(url=f"{self._uri}/agents")
            response.raise_for_status()
            data = response.json()
            return [AgentResponse(**item) for item in data["items"]]

    def post_agent(self, biscuit: TheoriqBiscuit, content: bytes) -> AgentResponse:
        url = f"{self._uri}/agents"
        headers = biscuit.to_headers()
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(url=url, content=content, headers=headers)
            response.raise_for_status()
            return AgentResponse.model_validate(response.json())

    def patch_agent(self, biscuit: TheoriqBiscuit, content: bytes, agent_id: str) -> AgentResponse:
        url = f"{self._uri}/agents/0x{agent_id.removeprefix('0x')}"
        headers = biscuit.to_headers()
        with httpx.Client(timeout=self._timeout) as client:
            response = client.patch(url=url, content=content, headers=headers)
            response.raise_for_status()
            return AgentResponse.model_validate(response.json())

    def delete_agent(self, biscuit: TheoriqBiscuit, agent_id: str) -> None:
        url = f"{self._uri}/agents/0x{agent_id.removeprefix('0x')}"
        headers = biscuit.to_headers()
        with httpx.Client(timeout=self._timeout) as client:
            response = client.delete(url=url, headers=headers)
            response.raise_for_status()

    def post_mint(self, biscuit: TheoriqBiscuit, agent_id: str) -> AgentResponse:
        url = f"{self._uri}/agents/0x{agent_id.removeprefix('0x')}/mint"
        headers = biscuit.to_headers()
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(url=url, headers=headers)
            response.raise_for_status()
            return AgentResponse.model_validate(response.json())

    def post_unmint(self, biscuit: TheoriqBiscuit, agent_id: str) -> AgentResponse:
        url = f"{self._uri}/agents/0x{agent_id.removeprefix('0x')}/unmint"
        headers = biscuit.to_headers()
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(url=url, headers=headers)
            response.raise_for_status()
            return AgentResponse.model_validate(response.json())

    def get_configuration(
        self, request_biscuit: RequestBiscuit, agent_address: AgentAddress, configuration_hash: str
    ) -> Dict[str, Any]:
        key = f"{agent_address.address}_{configuration_hash}"
        cached_response = self._config_cache.get(key)
        if cached_response:
            return cached_response

        headers = request_biscuit.to_headers()
        with httpx.Client(timeout=self._timeout) as client:
            response = client.get(url=f"{self._uri}/agents/{agent_address.address}/configuration", headers=headers)
            response.raise_for_status()
            configuration = response.json()
            if configuration is not None:
                self._config_cache.set(key, configuration)
            return configuration

    def post_request(
        self, request_biscuit: TheoriqBiscuit | RequestBiscuit, content: bytes, to_addr: str
    ) -> Dict[str, Any]:
        url = f'{self._uri}/agents/{to_addr.removeprefix("0x")}/execute'
        headers = request_biscuit.to_headers()
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(url=url, content=content, headers=headers)
            response.raise_for_status()
            return response.json()

    def post_configure(self, biscuit: TheoriqBiscuit, to_addr: str) -> Dict[str, Any]:
        url = f'{self._uri}/agents/{to_addr.removeprefix("0x")}/configure'
        headers = biscuit.to_headers()
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(url=url, headers=headers)
            response.raise_for_status()
            return response.json()

    def post_request_success(self, theoriq_biscuit: TheoriqBiscuit, response: Optional[str], agent: Agent) -> None:
        self._post_request_complete(theoriq_biscuit, response, agent, RequestStatus.SUCCESS)

    def post_request_failure(self, theoriq_biscuit: TheoriqBiscuit, response: Optional[str], agent: Agent) -> None:
        self._post_request_complete(theoriq_biscuit, response, agent, RequestStatus.FAILURE)

    def _post_request_complete(
        self, biscuit: TheoriqBiscuit, response: Optional[str], agent: Agent, status: RequestStatus
    ) -> None:
        request_fact = biscuit.read_fact(RequestFact)
        request_id = request_fact.request_id
        from_addr = request_fact.from_addr
        url = f"{self._uri}/requests/{request_id}/{status.value}"
        body = {"response": response}
        biscuit = self.attenuate_for_response(biscuit, body, request_id, from_addr, agent)
        headers = biscuit.to_headers()
        with httpx.Client(timeout=self._timeout) as client:
            r = client.post(url=url, json=body, headers=headers)
            r.raise_for_status()

    def post_request_complete(
        self, request_id: UUID, biscuit: TheoriqBiscuit, body: bytes, status: RequestStatus
    ) -> None:
        url = f"{self._uri}/requests/{request_id}/{status.value}"
        headers = biscuit.to_headers()
        with httpx.Client(timeout=self._timeout) as client:
            r = client.post(url=url, content=body, headers=headers)
            r.raise_for_status()

    def post_event(self, request_biscuit: RequestBiscuit, message: str) -> None:
        retry_delay = 1
        retry_count = 0
        prev_errors: List[Dict[str, Any]] = []

        headers = request_biscuit.to_headers()
        event_request = EventRequestBody(message=message, request_id=str(request_biscuit.request_facts.req_id))
        while retry_count <= self._max_retries:
            try:
                self._send_event(event_request, headers=headers)
                return
            except (httpx.TransportError, httpx.HTTPStatusError) as e:
                if retry_count == self._max_retries:
                    return
                prev_errors.append(
                    {
                        "attempt": retry_count + 1,
                        "error": e,
                        "datetime": datetime.now(timezone.utc).isoformat(),
                    }
                )
                retry_delay *= 2
                retry_count += 1

    def post_metrics(self, request_biscuit: RequestBiscuit, metrics: List[Metric]) -> None:
        url = f"{self._uri}/requests/{request_biscuit.request_facts.req_id}/metrics"
        headers = request_biscuit.to_headers()
        with httpx.Client(timeout=self._timeout) as client:
            client.post(url=url, json=MetricsRequestBody(metrics).to_dict(), headers=headers)

    def _send_event(self, request: EventRequestBody, headers: Dict[str, str]) -> None:
        url = f"{self._uri}/requests/{request.request_id.replace('-', '')}/events"
        with httpx.Client(timeout=self._timeout) as client:
            client.post(url=url, json=request.to_dict(), headers=headers)

    def post_notification(self, biscuit: TheoriqBiscuit, agent_id: str, notification: str) -> None:
        url = f"{self._uri}/agents/{agent_id}/notifications"
        headers = biscuit.to_headers()
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(url=url, content=notification, headers=headers)
            response.raise_for_status()

    def subscribe_to_agent_notifications(self, biscuit: TheoriqBiscuit, agent_id: str) -> Iterator[str]:
        CHUNK_SEP: Final[str] = "\n\n"

        url = f"{self._uri}/agents/{agent_id}/notifications"
        headers = biscuit.to_headers()
        with httpx.Client(timeout=self._timeout) as client:
            with client.stream("GET", url, headers=headers) as response:
                response.raise_for_status()
                buffer = ""
                for chunk in response.iter_text():
                    if not chunk or chunk.strip() == ":":
                        continue

                    buffer += chunk

                    # Process complete messages in buffer
                    while CHUNK_SEP in buffer:
                        message, buffer = buffer.split(CHUNK_SEP, 1)
                        if message.startswith("data: "):
                            payload = message[6:]  # remove the "data: " prefix
                            if payload.strip() != ":":
                                yield payload

    @classmethod
    def from_env(cls) -> ProtocolClient:
        uri: str = os.getenv("THEORIQ_URI", "") if is_protocol_secured() else "http://not_secured/test_only"
        if not uri.startswith("http"):
            raise ValueError(f"THEORIQ_URI `{uri}` is not a valid URI")

        result = cls(
            uri=uri,
            timeout=int(os.getenv("THEORIQ_TIMEOUT", "120")),
            max_retries=int(os.getenv("THEORIQ_MAX_RETRIES", "0")),
        )
        public_key = os.getenv("THEORIQ_PUBLIC_KEY")
        if public_key:
            cls._public_key_cache.set(
                f"{uri}/api/v1alpha2", PublicKeyResponse(**{"publicKey": public_key, "keyType": ""})
            )

        return result

    @staticmethod
    def attenuate_for_response(
        biscuit: TheoriqBiscuit, response: Dict[str, Any], request_id: UUID, from_addr: str, agent: Agent
    ) -> TheoriqBiscuit:
        config_response = ConfigureResponse(response=response)
        response_bytes = config_response.model_dump_json().encode()
        response_fact = ResponseFact(request_id=request_id, body_hash=PayloadHash(response_bytes), to_addr=from_addr)
        biscuit = agent.attenuate_biscuit(biscuit, response_fact)
        return biscuit
