import logging
from typing import Optional

from flask import Flask

from .system_health_filter import SystemHealthFilter
from ...logging import init
from ...logging import http_request_context


def init_logging(app: Flask, level: Optional[str] = None):
    init(level)
    app.before_request(http_request_context.before_request)
    app.after_request(http_request_context.after_request)

    flask_logger = logging.getLogger("werkzeug")
    flask_logger.setLevel(logging.WARNING)
