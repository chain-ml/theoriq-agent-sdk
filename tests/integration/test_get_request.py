import random
from datetime import datetime, timedelta, timezone

from theoriq.api.v1alpha2.manage import AgentManager


def test_get_requests(user_manager: AgentManager) -> None:
    requests = user_manager.get_requests(started_after=datetime.now(timezone.utc) - timedelta(days=1))
    assert requests["count"] > 0

    random_request_idx = random.randint(0, requests["count"] - 1)
    random_request = requests["items"][random_request_idx]
    random_request_id = random_request["id"]

    audit = user_manager.get_request_audit(random_request_id)

    assert audit["id"] == random_request_id
    assert "request" in audit
    assert "response" in audit
    assert "events" in audit
