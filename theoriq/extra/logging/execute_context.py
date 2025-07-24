from contextvars import ContextVar
from typing import ContextManager, Optional

from theoriq.api.common import ExecuteContextBase

from .http_request_context import x_request_id_var

biscuit_request_id: ContextVar[Optional[str]] = ContextVar("theoriq_request_id", default=None)


class ExecuteLogContext(ContextManager):
    def __init__(self, context: ExecuteContextBase, request_id_header: Optional[str] = None) -> None:
        self._token = biscuit_request_id.set(context.request_id)
        self._header_token = x_request_id_var.set(request_id_header) if request_id_header else None

    def __exit__(self, exc_type, exc_value, traceback, /):
        biscuit_request_id.reset(self._token)
        if self._header_token:
            x_request_id_var.reset(self._header_token)


def get_record_factory(old_factory):
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.theoriq_request_id = biscuit_request_id.get()
        return record

    return record_factory
