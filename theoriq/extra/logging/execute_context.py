from contextvars import ContextVar
from typing import ContextManager, Optional

from theoriq import ExecuteContext

request_id_var: ContextVar[Optional[str]] = ContextVar("theoriq_request_id", default=None)


class ExecuteLogContext(ContextManager):
    def __init__(self, context: ExecuteContext):
        self._token = request_id_var.set(context.request_id)

    def __exit__(self, exc_type, exc_value, traceback, /):
        request_id_var.reset(self._token)


def get_record_factory(old_factory):
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.theoriq_request_id = request_id_var.get()
        return record

    return record_factory
