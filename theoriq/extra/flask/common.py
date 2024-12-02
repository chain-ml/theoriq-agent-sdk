import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict

import flask
from flask import Blueprint, Request, Response, jsonify, request

from theoriq import Agent
from theoriq.api.common import ExecuteContextBase
from theoriq.api.v1alpha1.schemas import ChallengeRequestBody
from theoriq.biscuit import RequestBiscuit, RequestFacts, ResponseBiscuit, TheoriqBiscuitError
from theoriq.extra import start_time
from theoriq.extra.globals import agent_var
from theoriq.types import AgentDataObject
from theoriq.utils import is_protocol_secured

logger = logging.getLogger(__name__)


def theoriq_system_blueprint() -> Blueprint:
    blueprint = Blueprint("theoriq_system", __name__, url_prefix="/system")
    blueprint.add_url_rule("/challenge", view_func=sign_challenge, methods=["POST"])
    blueprint.add_url_rule("/agent", view_func=agent_data, methods=["GET"])
    blueprint.add_url_rule("/public-key", view_func=public_key, methods=["GET"])
    blueprint.add_url_rule("/livez", view_func=livez, methods=["GET"])
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
            path = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), path))
            logger.debug(f"loading metadata file: {path}")
            agent_data = AgentDataObject.from_yaml(path)
            data = agent_data.to_dict()
            metadata = data["spec"] | {"name": agent_data.metadata.name}
        except Exception:
            pass

    result = {"system": result} | {"metadata": metadata}
    return jsonify(result)


def process_biscuit_request(agent: Agent, protocol_public_key: str, req: Request) -> RequestBiscuit:
    """
    Retrieve and process the request biscuit

    :param agent: Agent processing the biscuit
    :param protocol_public_key: Public key of the protocol
    :param req: http request received by the agent
    :return: RequestBiscuit
    :raises: If the biscuit could not be processed, a flask response is returned with the 401 status code.
    """
    if is_protocol_secured():
        token = get_bearer_token(req)
        request_biscuit = RequestBiscuit.from_token(token=token, public_key=protocol_public_key)
        agent.verify_biscuit(request_biscuit, req.data)
    else:
        address = str(agent.config.address)
        biscuit = RequestFacts.generate_new_biscuit(req.data, from_addr=address, to_addr=address)
        request_biscuit = RequestBiscuit(biscuit)
    return request_biscuit


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


def build_error_payload(*, agent_address: str, request_id: str, err: str, status_code: int) -> flask.Response:
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


def new_error_response(context: ExecuteContextBase, body: Exception, status_code: int) -> flask.Response:
    error_response = build_error_payload(
        agent_address=context.agent_address, request_id=context.request_id, err=str(body), status_code=status_code
    )
    response_biscuit = context.new_error_response_biscuit(error_response.get_data())
    return add_biscuit_to_response(error_response, response_biscuit)
