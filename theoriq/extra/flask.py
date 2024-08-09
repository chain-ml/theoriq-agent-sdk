"""Helpers to write agent using a flask web app."""

import flask
import pydantic
from flask import Blueprint, Request, Response, jsonify, request

from ..agent import Agent, AgentConfig
from ..biscuit import RequestBiscuit, ResponseBiscuit, TheoriqBiscuitError, TheoriqCost
from ..execute import ExecuteRequest, ExecuteRequestFn
from ..extra.globals import agent_var
from ..schemas import ChallengeRequestBody, ExecuteRequestBody
from ..types.currency import Currency


def theoriq_blueprint(agent_config: AgentConfig, execute_fn: ExecuteRequestFn) -> Blueprint:
    """
    Theoriq blueprint
    :return: a blueprint with all the routes required by the `theoriq` protocol
    """

    main_blueprint = Blueprint("main_blueprint", __name__)

    @main_blueprint.before_request
    def set_context():
        agent_var.set(Agent(agent_config))

    v1alpha1_blue_print = Blueprint("v1alpha1", __name__, url_prefix="/api/v1alpha1")
    v1alpha1_blue_print.add_url_rule("/execute", view_func=lambda: execute(execute_fn), methods=["POST"])
    v1alpha1_blue_print.register_blueprint(theoriq_system_blueprint())
    main_blueprint.register_blueprint(v1alpha1_blue_print)

    v1alpha2_blueprint = Blueprint("v1alpha2", __name__, url_prefix="/api/v1alpha2")
    v1alpha2_blueprint.add_url_rule("/execute", view_func=lambda: execute(execute_fn), methods=["POST"])
    v1alpha2_blueprint.register_blueprint(theoriq_system_blueprint())

    main_blueprint.register_blueprint(v1alpha2_blueprint)
    return main_blueprint


def theoriq_system_blueprint() -> Blueprint:
    blueprint = Blueprint("theoriq_system", __name__, url_prefix="/system")
    blueprint.add_url_rule("/challenge", view_func=sign_challenge, methods=["POST"])
    blueprint.add_url_rule("/public-key", view_func=public_key, methods=["GET"])

    return blueprint


def public_key() -> Response:
    """Public key endpoint"""
    agent = agent_var.get()
    public_key = agent.public_key
    return jsonify({"publicKey": public_key, "keyType": "ed25519", "keccak256Hash": str(agent.config.agent_address)})


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


def process_biscuit_request(agent: Agent, req: Request) -> RequestBiscuit:
    """
    Retrieve and process the request biscuit

    :param agent: Agent processing the biscuit
    :param request: http request received by the agent
    :return: RequestBiscuit
    :raises: If the biscuit could not be processed, a flask response is returned with the 401 status code.
    """
    try:
        bearer_token = get_bearer_token(req)
        return agent.parse_and_verify_biscuit(bearer_token, req.data)
    except TheoriqBiscuitError as err:
        flask.abort(401, err)


def get_bearer_token(req: Request) -> str:
    """Get the bearer token from the request"""
    authorization = req.headers.get("Authorization")
    if not authorization:
        raise TheoriqBiscuitError("Authorization header is missing")
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
