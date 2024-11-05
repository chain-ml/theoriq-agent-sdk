"""Helpers to write agent using a flask web app."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import flask
import pydantic
from flask import Blueprint, Request, Response, jsonify, request
from theoriq.biscuit import AgentAddress
from theoriq.types import AgentDataObject

from ..agent import Agent, AgentConfig
from ..biscuit import RequestBiscuit, RequestFacts, ResponseBiscuit, TheoriqBiscuitError
from ..execute import ExecuteContext, ExecuteRequestFn, ExecuteRuntimeError
from ..extra.globals import agent_var
from theoriq.api_v1alpha1.protocol import ProtocolClient
from theoriq.api_v1alpha1.schemas import ChallengeRequestBody, ExecuteRequestBody
from . import start_time

logger = logging.getLogger(__name__)


def theoriq_blueprint(
    agent_config: AgentConfig, execute_fn: ExecuteRequestFn, schema: Optional[Dict] = None
) -> Blueprint:
    """
    Theoriq blueprint
    :return: a blueprint with all the routes required by the `theoriq` protocol
    """

    main_blueprint = Blueprint("main_blueprint", __name__)
    Agent.validate_schema(schema)

    @main_blueprint.before_request
    def set_context():
        agent_var.set(Agent(agent_config, schema))

    v1alpha1_blue_print = Blueprint("v1alpha1", __name__, url_prefix="/api/v1alpha1")
    v1alpha1_blue_print.add_url_rule("/execute", view_func=lambda: execute(execute_fn), methods=["POST"])
    v1alpha1_blue_print.register_blueprint(theoriq_system_blueprint())
    v1alpha1_blue_print.register_blueprint(theoriq_configuration_blueprint())
    main_blueprint.register_blueprint(v1alpha1_blue_print)

    v1alpha2_blueprint = Blueprint("v1alpha2", __name__, url_prefix="/api/v1alpha2")
    v1alpha2_blueprint.add_url_rule("/execute", view_func=lambda: execute(execute_fn), methods=["POST"])
    v1alpha2_blueprint.register_blueprint(theoriq_system_blueprint())
    v1alpha2_blueprint.register_blueprint(theoriq_configuration_blueprint())
    main_blueprint.register_blueprint(v1alpha2_blueprint)

    return main_blueprint


def theoriq_system_blueprint() -> Blueprint:
    blueprint = Blueprint("theoriq_system", __name__, url_prefix="/system")
    blueprint.add_url_rule("/challenge", view_func=sign_challenge, methods=["POST"])
    blueprint.add_url_rule("/agent", view_func=agent_data, methods=["GET"])
    blueprint.add_url_rule("/public-key", view_func=public_key, methods=["GET"])
    blueprint.add_url_rule("/livez", view_func=livez, methods=["GET"])
    return blueprint


def theoriq_configuration_blueprint() -> Blueprint:
    blueprint = Blueprint("theoriq_configuration", __name__, url_prefix="/configuration")
    blueprint.add_url_rule("/schema", view_func=get_configuration_schema, methods=["GET"])
    return blueprint


def livez() -> Response:
    return jsonify({"startTime": start_time})


def public_key() -> Response:
    """Public key endpoint"""
    agent = agent_var.get()
    return jsonify({"publicKey": agent.public_key, "keyType": "ed25519", "keccak256Hash": str(agent.config.address)})


def sign_challenge() -> Response:
    """Sign endpoint"""
    challenge_body = ChallengeRequestBody.model_validate(request.json)
    nonce_bytes = bytes.fromhex(challenge_body.nonce)
    signature = agent_var.get().sign_challenge(nonce_bytes)
    return jsonify({"signature": f"0x{signature.hex()}", "nonce": challenge_body.nonce})


def agent_data() -> Response:
    """Agent data endpoint"""
    agent = agent_var.get()
    path = agent.config.agent_yaml_path
    result: Dict[str, Any] = {"publicKey": agent.public_key}
    metadata = {}

    if path:
        try:
            agent_data = AgentDataObject.from_yaml(path)
            data = agent_data.to_dict()
            metadata = data["spec"] | {"name": agent_data.metadata.name}
        except Exception:
            pass

    result = {"system": result} | {"metadata": metadata}
    return jsonify(result)


def execute(execute_request_function: ExecuteRequestFn) -> Response:
    """Execute endpoint"""
    logger.debug("Executing request")
    logger.debug(request.json)
    agent = agent_var.get()
    try:
        execute_request_body = ExecuteRequestBody.model_validate(request.json)
        configuration = execute_request_body.configuration
        if configuration is not None:
            agent.virtual_address = AgentAddress(configuration.fromRef.id)
        execute_context = _get_execute_context(agent)
        try:
            # Execute user's function
            try:
                execute_response = execute_request_function(execute_context, execute_request_body)
            except ExecuteRuntimeError as err:
                execute_response = execute_context.runtime_error_response(err)

            response = jsonify(execute_response.body.to_dict())
            response_biscuit = execute_context.new_response_biscuit(response.get_data(), execute_response.theoriq_cost)
            response = add_biscuit_to_response(response, response_biscuit)
        except pydantic.ValidationError as err:
            response = new_error_response(execute_context, err, 400)
        except Exception as err:
            logger.exception(err)
            response = new_error_response(execute_context, err, 500)
    except TheoriqBiscuitError as err:
        # Process the request biscuit. If not present, return a 401 error
        return _build_error_payload(
            agent_address=str(agent.config.address), request_id="", err=str(err), status_code=401
        )
    except Exception as err:
        return _build_error_payload(
            agent_address=str(agent.config.address), request_id="", err=str(err), status_code=500
        )
    else:
        return response


def get_configuration_schema() -> Response:
    agent = agent_var.get()
    return jsonify(agent.schema or {})


def _get_execute_context(agent: Agent) -> ExecuteContext:
    protocol_client = ProtocolClient.from_env()
    request_biscuit = _process_biscuit_request(agent, protocol_client.public_key, request)
    return ExecuteContext(agent, protocol_client, request_biscuit)


def _process_biscuit_request(agent: Agent, protocol_public_key: str, req: Request) -> RequestBiscuit:
    """
    Retrieve and process the request biscuit

    :param agent: Agent processing the biscuit
    :param protocol_public_key: Public key of the protocol
    :param req: http request received by the agent
    :return: RequestBiscuit
    :raises: If the biscuit could not be processed, a flask response is returned with the 401 status code.
    """
    if ProtocolClient.is_secured():
        token = _get_bearer_token(req)
        request_biscuit = RequestBiscuit.from_token(token=token, public_key=protocol_public_key)
        agent.verify_biscuit(request_biscuit, req.data)
    else:
        address = str(agent.config.address)
        biscuit = RequestFacts.generate_new_biscuit(req.data, from_addr=address, to_addr=address)
        request_biscuit = RequestBiscuit(biscuit)
    return request_biscuit


def _get_bearer_token(req: Request) -> str:
    """Get the bearer token from the request"""
    authorization = req.headers.get("Authorization")
    if not authorization:
        raise TheoriqBiscuitError("Authorization header is missing")
    else:
        return authorization[len("bearer ") :]


def add_biscuit_to_response(response: flask.Response, resp_biscuit: ResponseBiscuit) -> flask.Response:
    response.headers.add("authorization", f"bearer {resp_biscuit.to_base64()}")
    return response


def new_error_response(context: ExecuteContext, body: Exception, status_code: int) -> flask.Response:
    error_response = _build_error_payload(
        agent_address=context.agent_address, request_id=context.request_id, err=str(body), status_code=status_code
    )
    response_biscuit = context.new_error_response_biscuit(error_response.get_data())
    return add_biscuit_to_response(error_response, response_biscuit)


def _build_error_payload(*, agent_address: str, request_id: str, err: str, status_code: int) -> flask.Response:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "error": err,
        "source": agent_address,
        "status": str(status_code),
    }
    if request_id:
        payload["requestId"] = request_id
    error_response = jsonify(payload)
    error_response.status = str(status_code)
    return error_response
