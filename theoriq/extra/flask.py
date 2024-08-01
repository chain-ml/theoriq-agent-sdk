"""Helpers to write agent using a flask web app."""

import flask
import pydantic
from flask import Blueprint, Response, jsonify, request
from theoriq.agent import Agent, AgentConfig
from theoriq.error import AuthorizationError, ParseBiscuitError, VerificationError
from theoriq.execute import ExecuteRequest, ExecuteRequestFn
from theoriq.extra.globals import agent_var
from theoriq.facts import Currency, TheoriqCost
from theoriq.schemas import ChallengeRequestBody, ExecuteRequestBody
from theoriq.types import RequestBiscuit, ResponseBiscuit


def theoriq_blueprint(agent_config: AgentConfig, execute_fn: ExecuteRequestFn) -> Blueprint:
    """
    Theoriq blueprint
    :return: a blueprint with all the routes required by the `theoriq` protocol
    """

    main_blueprint = Blueprint("main_blueprint", __name__)

    backward_compatible_blueprint = Blueprint("old_theoriq", __name__, url_prefix="/api/v1alpha1")
    backward_compatible_blueprint.add_url_rule(
        "/behaviors/chat-completion", view_func=lambda: execute(execute_fn), methods=["POST"]
    )
    main_blueprint.register_blueprint(backward_compatible_blueprint)

    theoriq_blueprint = Blueprint("theoriq", __name__, url_prefix="/theoriq/api/v1alpha1")

    @main_blueprint.before_request
    def set_context():
        agent_var.set(Agent(agent_config))

    theoriq_blueprint.register_blueprint(theoriq_system_blueprint())
    theoriq_blueprint.add_url_rule("/execute", view_func=lambda: execute(execute_fn), methods=["POST"])
    main_blueprint.register_blueprint(theoriq_blueprint)

    return main_blueprint


def theoriq_system_blueprint() -> Blueprint:
    blueprint = Blueprint("theoriq_system", __name__, url_prefix="/system")
    blueprint.add_url_rule("/challenge", view_func=sign_challenge, methods=["POST"])

    return blueprint


def sign_challenge() -> Response:
    """Sign endpoint"""
    challenge_body = ChallengeRequestBody.model_validate(request.json)
    nonce_bytes = bytes.fromhex(challenge_body.nonce)
    signature = agent_var.get().sign_challenge(nonce_bytes)
    return jsonify({"signature": signature.hex(), "nonce": challenge_body.nonce})


def execute(execute_request_function: ExecuteRequestFn) -> Response:
    """Execute endpoint"""
    agent = agent_var.get()

    # Process the request biscuit. If not present, return a 401 error
    request_biscuit = process_biscuit_request(agent, request)

    try:
        # Execute user's function
        execute_request_body = ExecuteRequestBody.model_validate(request.json)
        execute_request = ExecuteRequest(execute_request_body, request_biscuit)
        execute_response = execute_request_function(execute_request)

        response = jsonify(execute_response.body.to_dict())
        response_biscuit = new_response_biscuit(agent, request_biscuit, response, execute_response.theoriq_cost)
        response = add_biscuit_to_response(response, response_biscuit)
    except pydantic.ValidationError as err:
        response = new_error_response(agent, request_biscuit, 400, err)
    except Exception as err:
        response = new_error_response(agent, request_biscuit, 500, err)

    return response


def process_biscuit_request(agent: Agent, request: flask.Request) -> RequestBiscuit:
    """
    Retrieve and process the request biscuit

    :param agent: Agent processing the biscuit
    :param request: http request received by the agent
    :return: RequestBiscuit
    :raises: If the biscuit could not be processed, a flask response is returned with the 401 status code.
    """
    try:
        bearer_token = get_bearer_token(request)
        request_body = request.data
        return agent.parse_and_verify_biscuit(bearer_token, request_body)
    except (ParseBiscuitError, VerificationError, AuthorizationError) as err:
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
    """Build a biscuit for the response to an 'execute' request."""
    resp_body = response.get_data()
    return agent.attenuate_biscuit_for_response(req_biscuit, resp_body, cost)


def add_biscuit_to_response(response: flask.Response, resp_biscuit: ResponseBiscuit) -> flask.Response:
    response.headers.add("authorization", f"bearer {resp_biscuit.to_base64()}")
    return response


def new_error_response(agent: Agent, req_biscuit: RequestBiscuit, status_code: int, body: Exception) -> flask.Response:
    response = jsonify({"error": str(body)})
    response.status = str(status_code)
    resp_biscuit = new_response_biscuit(agent, req_biscuit, response, TheoriqCost.zero(Currency.USDC))
    return add_biscuit_to_response(response, resp_biscuit)
