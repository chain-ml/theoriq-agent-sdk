import uuid
from contextvars import ContextVar
from typing import Optional

from flask import Response, request

import logging

x_request_id_var: ContextVar[Optional[str]] = ContextVar("x_request_id", default=None)
logger = logging.getLogger(__name__)

def before_request():
    x_request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    x_request_id_var.set(x_request_id)


def after_request(response: Response) -> Response:
    is_health = request.method == "GET" and response.status_code == 200 and "system/livez" in request.path
    logger.log(logging.DEBUG if is_health else logging.INFO, f"{request.method} {request.path} {response.status_code}")
    x_request_id_var.set(None)
    return response


def get_record_factory(old_factory):
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.x_request_id = x_request_id_var.get()
        return record

    return record_factory
