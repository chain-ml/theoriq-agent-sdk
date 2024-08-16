"""Helpers to write agent using a flask web app."""

import os
from typing import Any, Dict

import flask
import pydantic
from flask import Blueprint, Request, Response, jsonify, request
from theoriq.types import AgentDataObject

from ..agent import Agent, AgentConfig
from ..biscuit import RequestBiscuit, ResponseBiscuit, TheoriqBiscuitError
from ..execute import ExecuteContext, ExecuteRequestFn
from ..extra.globals import agent_var
from ..protocol import ProtocolClient
from ..schemas import ChallengeRequestBody, ExecuteRequestBody


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
    blueprint.add_url_rule("/agent", view_func=agent_data, methods=["GET"])
    blueprint.add_url_rule("/public-key", view_func=public_key, methods=["GET"])
    return blueprint


def public_key() -> Response:
    """Public key endpoint"""
    agent = agent_var.get()
    return jsonify({"publicKey": agent.public_key, "keyType": "ed25519", "keccak256Hash": str(agent.config.address)})


def sign_challenge() -> Response:
    """Sign endpoint"""
    challenge_body = ChallengeRequestBody.model_validate(request.json)
    nonce_bytes = bytes.fromhex(challenge_body.nonce)
    signature = agent_var.get().sign_challenge(nonce_bytes)
    return jsonify({"signature": signature.hex(), "nonce": challenge_body.nonce})


def agent_data() -> Response:
    """Agent data endpoint"""
    path = os.getenv("AGENT_YAML_PATH")
    try:
        agent = agent_var.get()
        result: Dict[str, Any] = {"publicKey": agent.public_key}
        metadata = {}
        if path:
            agent_data = AgentDataObject.from_yaml(path)
            data = agent_data.to_dict()
            metadata = data["spec"] | {"name": agent_data.metadata.name}
        result = {"system": result} | {"metadata": metadata}
        return jsonify(result)
    except Exception:
        return Response(status=501)


def execute(execute_request_function: ExecuteRequestFn) -> Response:
    """Execute endpoint"""
    agent = agent_var.get()
    protocol_client = ProtocolClient.from_env()

    # Process the request biscuit. If not present, return a 401 error
    request_biscuit = process_biscuit_request(agent, protocol_client.public_key, request)
    execute_context = ExecuteContext(agent, protocol_client, request_biscuit)

    try:
        # Execute user's function
        execute_request_body = ExecuteRequestBody.model_validate(request.json)
        execute_response = execute_request_function(execute_context, execute_request_body)

        response = jsonify(execute_response.body.to_dict())
        response_biscuit = execute_context.new_response_biscuit(response.get_data(), execute_response.theoriq_cost)
        response = add_biscuit_to_response(response, response_biscuit)
    except pydantic.ValidationError as err:
        response = new_error_response(execute_context, 400, err)
    except Exception as err:
        response = new_error_response(execute_context, 500, err)

    return response


def process_biscuit_request(agent: Agent, protocol_public_key: str, req: Request) -> RequestBiscuit:
    """
    Retrieve and process the request biscuit

    :param agent: Agent processing the biscuit
    :param req: http request received by the agent
    :return: RequestBiscuit
    :raises: If the biscuit could not be processed, a flask response is returned with the 401 status code.
    """
    try:
        bearer_token = get_bearer_token(req)
        request_biscuit = RequestBiscuit.from_token(token=bearer_token, public_key=protocol_public_key)
        agent.verify_biscuit(request_biscuit, req.data)
        return request_biscuit
    except TheoriqBiscuitError as err:
        flask.abort(401, err)


def get_bearer_token(req: Request) -> str:
    """Get the bearer token from the request"""
    authorization = req.headers.get("Authorization")
    if not authorization:
        raise TheoriqBiscuitError("Authorization header is missing")
    else:
        return authorization[len("bearer ") :]


def add_biscuit_to_response(response: flask.Response, resp_biscuit: ResponseBiscuit) -> flask.Response:
    response.headers.add("authorization", f"bearer {resp_biscuit.to_base64()}")
    return response


def new_error_response(execute_context: ExecuteContext, status_code: int, body: Exception) -> flask.Response:
    error_response = jsonify({"error": str(body)})
    response_biscuit = execute_context.new_error_response_biscuit(error_response.get_data())
    error_response.status = str(status_code)
    return add_biscuit_to_response(error_response, response_biscuit)
