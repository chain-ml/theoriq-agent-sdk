import logging
from typing import Optional, Union

from flask import Flask

from ..logging import http_request_context, init


def init_logging(app: Flask, level: Optional[Union[str, int]] = None, force: bool = False) -> None:
    init(level, force)
    app.before_request(http_request_context.before_request)
    app.after_request(http_request_context.after_request)

    flask_logger = logging.getLogger("werkzeug")
    flask_logger.setLevel(logging.WARNING)


def list_routes(app: Flask) -> None:
    logging.info("registered endpoints:")
    for rule in app.url_map.iter_rules():
        methods = ",".join(rule.methods) if rule.methods else None
        logging.info(f'path="{rule.rule}" methods="{methods}"')
