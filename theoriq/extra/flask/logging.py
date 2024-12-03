import logging
from typing import Optional

from flask import Flask

from ..logging import init
from ..logging import http_request_context


def init_logging(app: Flask, level: Optional[str] = None):
    init(level)
    app.before_request(http_request_context.before_request)
    app.after_request(http_request_context.after_request)

    flask_logger = logging.getLogger("werkzeug")
    flask_logger.setLevel(logging.WARNING)


def list_routes(app: Flask):
    logging.info(f"registered endpoints:")
    for rule in app.url_map.iter_rules():
        logging.info(f'path="{rule.rule}" methods="{",".join(rule.methods)}"')
