from typing import Optional, Union

from flask import Blueprint, Flask

from .logging import init_logging, list_routes


def run_agent_flask_app(
    theoriq_bluprint: Blueprint,
    port: int,
    host: str = "0.0.0.0",
    name: Optional[str] = None,
    logging_level: Optional[Union[str, int]] = None,
    force_logging: bool = False,
) -> None:
    app = Flask(name or f"Agent on port {port}")
    app.register_blueprint(theoriq_bluprint)

    if logging_level is not None:
        init_logging(app, level=logging_level, force=force_logging)
        list_routes(app)

    app.run(host=host, port=port)
