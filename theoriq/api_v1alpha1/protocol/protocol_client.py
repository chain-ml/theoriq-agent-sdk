from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

import httpx

from theoriq.biscuit import RequestBiscuit

from ...types import Metric
from ..schemas.agent import AgentResponse
from ..schemas.api import PublicKeyResponse
from ..schemas.event_request import EventRequestBody
from ..schemas.metrics import MetricsRequestBody


class ProtocolClient:

    def __init__(self, uri: str, timeout: Optional[int] = 120, max_retries: Optional[int] = None):
        self._uri = f"{uri}/api/v1alpha1"
        self._timeout = timeout
        self._max_retries = max_retries or 0
        self._public_key: Optional[str] = None

    @property
    def public_key(self) -> str:
        if self._public_key is None:
            self._public_key = self.get_public_key().public_key
        return self._public_key

    def get_public_key(self) -> PublicKeyResponse:
        with httpx.Client(timeout=self._timeout) as client:
            response = client.get(url=f"{self._uri}/auth/biscuits/public-key")
            response.raise_for_status()
            data = response.json()
            return PublicKeyResponse(**data)

    def get_agents(self) -> Sequence[AgentResponse]:
        with httpx.Client(timeout=self._timeout) as client:
            response = client.get(url=f"{self._uri}/agents")
            response.raise_for_status()
            data = response.json()
            return [AgentResponse(**item) for item in data["items"]]

    def post_request(self, request_biscuit: RequestBiscuit, content: bytes, to_addr: str):
        url = f'{self._uri}/agents/{to_addr.removeprefix("0x")}/execute'
        headers = request_biscuit.to_headers()
        headers = headers | {"X-AP-AGENT-REQUEST-PATH": "/api/v1alpha1/execute", "X-AP-AGENT-REQUEST-METHOD": "POST"}
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(url=url, content=content, headers=headers)
            return response.json()

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
        url = f"{self._uri}/requests/execute-{request_biscuit.request_facts.req_id}/metrics"
        headers = request_biscuit.to_headers()
        with httpx.Client(timeout=self._timeout) as client:
            client.post(url=url, json=MetricsRequestBody(metrics).to_dict(), headers=headers)

    def _send_event(self, request: EventRequestBody, headers: Dict[str, str]) -> None:
        url = f"{self._uri}/requests/execute-{request.request_id.replace('-', '')}/events"
        with httpx.Client(timeout=self._timeout) as client:
            client.post(url=url, json=request.to_dict(), headers=headers)

    @classmethod
    def from_env(cls) -> ProtocolClient:
        uri: str = os.getenv("THEORIQ_URI", "") if cls.is_secured() else "http://not_secured/test_only"
        if not uri.startswith("http"):
            raise ValueError(f"THEORIQ_URI `{uri}` is not a valid URI")

        result = cls(
            uri=uri,
            timeout=int(os.getenv("THEORIQ_TIMEOUT", "120")),
            max_retries=int(os.getenv("THEORIQ_MAX_RETRIES", "0")),
        )
        result._public_key = os.getenv("THEORIQ_PUBLIC_KEY")
        return result

    @classmethod
    def is_secured(cls) -> bool:
        return os.getenv("THEORIQ_SECURED", "true").lower() == "true"
