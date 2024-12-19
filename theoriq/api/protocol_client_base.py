from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from theoriq.biscuit import AgentAddress, RequestBiscuit
from theoriq.types import Metric
from theoriq.utils import TTLCache, is_protocol_secured


class ProtocolClientBase:
    _public_key_cache: TTLCache[Any] = TTLCache(ttl=None, max_size=5)

    def __init__(self, uri: str, api_version: str, timeout: Optional[int] = 120, max_retries: Optional[int] = None):
        self._uri = f"{uri}/api/{api_version}"
        self._timeout = timeout
        self._max_retries = max_retries or 0

    @property
    def public_key(self) -> str:
        """
        Get the cached public key or fetch a new one if not available.

        Returns:
            str: The public key string.

        Note:
            The key is cached using the URI as the cache key to avoid redundant API calls.
        """
        try:
            key = self._public_key_cache.get(self._uri)
            if key is None:
                key = self.get_public_key()
                self._public_key_cache.set(self._uri, key)
            return key.public_key
        except (httpx.TransportError, httpx.HTTPStatusError) as e:
            raise RuntimeError(f"Failed to get public key: {str(e)}") from e

    def get_public_key(self) -> PublicKeyResponse:
        with httpx.Client(timeout=self._timeout) as client:
            response = client.get(url=f"{self._uri}/auth/biscuits/public-key")
            response.raise_for_status()
            data = response.json()
            return PublicKeyResponse(**data)

    def _make_request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """Make an HTTP request with retries."""
        url = f"{self._uri}/{endpoint.lstrip('/')}"
        with httpx.Client(timeout=self._timeout) as client:
            response = getattr(client, method)(url=url, **kwargs)
            response.raise_for_status()
            return response