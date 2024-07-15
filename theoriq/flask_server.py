from flask import Flask, Blueprint, request, jsonify
from contextvars import ContextVar

from theoriq.agent import Agent, AgentConfig


agent_var = ContextVar("agent")


def theoriq_blueprint(agent_config: AgentConfig) -> Blueprint:
    """
    Theoriq blueprint
    :return: a blueprint with all the routes required by the `theoriq` protocol
    """

    blueprint = Blueprint("theoriq", __name__, url_prefix="/theoriq/api/v1alpha1")

    @blueprint.before_request
    def set_context():
        agent_var.set(Agent(agent_config))

    blueprint.register_blueprint(theoriq_system_blueprint())

    return blueprint


def theoriq_system_blueprint() -> Blueprint:
    blueprint = Blueprint("theoriq_system", __name__, url_prefix="/system")
    blueprint.add_url_rule("/challenge", view_func=sign_challenge, methods=["POST"])

    return blueprint


def sign_challenge():
    json_body = request.json
    nonce: str = json_body["nonce"]
    nonce_bytes = bytes.fromhex(nonce)
    signature = agent_var.get().sign_challenge(nonce_bytes)
    return jsonify({
        "signature": signature.hex(),
        "nonce": nonce
    })
