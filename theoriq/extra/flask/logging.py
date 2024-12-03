import logging
from typing import Optional

from flask import Flask

from ..logging import http_request_context, init


def init_logging(app: Flask, level: Optional[str] = None):
    init(level)
    app.before_request(http_request_context.before_request)
    app.after_request(http_request_context.after_request)

    flask_logger = logging.getLogger("werkzeug")
    flask_logger.setLevel(logging.WARNING)


def list_routes(app: Flask):
    logging.info("registered endpoints:")
    for rule in app.url_map.iter_rules():
        methods = ",".join(rule.methods) if rule.methods else None
        logging.info(f'path="{rule.rule}" methods="{methods}"')
