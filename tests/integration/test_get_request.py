import random
from datetime import datetime, timedelta, timezone

from theoriq.api.v1alpha2.manage import AgentManager
from theoriq.api.v1alpha2.schemas import RequestAudit, RequestItem


def test_get_requests(user_manager: AgentManager) -> None:
    requests = user_manager.get_requests(started_after=datetime.now(timezone.utc) - timedelta(days=1))
    assert len(requests) > 0
    assert isinstance(requests[0], RequestItem)

    random_request_idx = random.randint(0, len(requests) - 1)
    random_request = requests[random_request_idx]
    random_request_id = random_request.id

    audit = user_manager.get_request_audit(random_request_id)

    assert isinstance(audit, RequestAudit)
    assert audit.id == random_request_id
