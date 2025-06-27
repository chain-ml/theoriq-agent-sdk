from datetime import datetime, timedelta, timezone

import pytest

from theoriq.api.v1alpha2 import ProtocolClient
from theoriq.api.v1alpha2.protocol.biscuit_provider import BiscuitProviderFromAPIKey
from theoriq.utils import must_read_env_str


@pytest.fixture
def client() -> ProtocolClient:
    return ProtocolClient("http://localhost:8080")


@pytest.fixture
def biscuit_provider(client: ProtocolClient) -> BiscuitProviderFromAPIKey:
    return BiscuitProviderFromAPIKey(must_read_env_str("THEORIQ_API_KEY"), client=client)


def test_get_public_key(client: ProtocolClient) -> None:
    pub_key = client.get_public_key()
    assert pub_key.key_type == "ed25519"


def test_create_api_key(client: ProtocolClient, biscuit_provider: BiscuitProviderFromAPIKey) -> None:
    expires_at = datetime.now(tz=timezone.utc) + timedelta(minutes=1)
    response = client.create_api_key(biscuit_provider.get_biscuit(), expires_at)

    assert isinstance(response["biscuit"], str)
    assert response["data"]["expiresAt"] == int(expires_at.timestamp())
