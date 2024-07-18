"""Helpers to write agent using a flask web app."""

import flask
from flask import Blueprint, request, jsonify, Response

from theoriq.agent import Agent, AgentConfig
from theoriq.error import VerificationError, ParseBiscuitError
from theoriq.execute import ExecuteFn, ExecuteRequest
from theoriq.facts import TheoriqCost
from theoriq.schemas import ChallengeRequestBody, ExecuteRequestBody
from theoriq.types import RequestBiscuit, ResponseBiscuit

from theoriq_extra.globals import agent_var


def theoriq_blueprint(agent_config: AgentConfig, execute_fn: ExecuteFn) -> Blueprint:
    """
    Theoriq blueprint
    :return: a blueprint with all the routes required by the `theoriq` protocol
    """

    blueprint = Blueprint("theoriq", __name__, url_prefix="/theoriq/api/v1alpha1")

    @blueprint.before_request
    def set_context():
        agent_var.set(Agent(agent_config))

    blueprint.register_blueprint(theoriq_system_blueprint())
    blueprint.add_url_rule("/execute", view_func=lambda: execute(execute_fn), methods=["POST"])

    return blueprint


def theoriq_system_blueprint() -> Blueprint:
    blueprint = Blueprint("theoriq_system", __name__, url_prefix="/system")
    blueprint.add_url_rule("/challenge", view_func=sign_challenge, methods=["POST"])

    return blueprint


def sign_challenge():
    """Sign endpoint"""
    challenge_body = ChallengeRequestBody.model_validate(request.json)
    nonce_bytes = bytes.fromhex(challenge_body.nonce)
    signature = agent_var.get().sign_challenge(nonce_bytes)
    return jsonify({"signature": signature.hex(), "nonce": challenge_body.nonce})


def execute(func: ExecuteFn) -> Response:
    """Execute endpoint"""
    agent = agent_var.get()

    # Validate the execute request
    req_biscuit = process_biscuit_request(agent, request)
    execute_request_body = ExecuteRequestBody.model_validate(request.json)

    # Make sure that the execute_request_var is available when running the `func` callable.
    execute_request = ExecuteRequest(execute_request_body, req_biscuit)

    # Execute user's function
    execute_response = func(execute_request)

    flask_response = jsonify(execute_response.body.dict())
    resp_biscuit = new_response_biscuit(agent, req_biscuit, flask_response, execute_response.theoriq_cost)
    response = add_biscuit_to_response(flask_response, resp_biscuit)

    return response


def process_biscuit_request(agent: Agent, request: flask.Request) -> RequestBiscuit:
    try:
        bearer_token = get_bearer_token(request)
        request_body = request.data
        return agent.parse_and_verify_biscuit(bearer_token, request_body)
    except (ParseBiscuitError, VerificationError) as err:
        raise flask.abort(401, err)


def get_bearer_token(request: flask.Request) -> str:
    """Get the bearer token from the request"""
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise VerificationError("Authorization header is missing")
    else:
        return authorization[len("bearer ") :]


def new_response_biscuit(
    agent: Agent, req_biscuit: RequestBiscuit, response: flask.Response, cost: TheoriqCost
) -> ResponseBiscuit:
    resp_body = response.get_data()
    return agent.attenuate_biscuit_for_response(req_biscuit, resp_body, cost)


def add_biscuit_to_response(response: flask.Response, resp_biscuit: ResponseBiscuit) -> flask.Response:
    response.headers.add("authorization", f"bearer {resp_biscuit.to_base64()}")
    return response
