from datetime import timezone, datetime
from typing import Callable

import flask
from flask import Blueprint, request, jsonify
from contextvars import ContextVar

from theoriq.agent import Agent, AgentConfig
from theoriq.error import VerificationError, ParseBiscuitError
from theoriq.facts import TheoriqCost
from theoriq.schemas import DialogItem, DialogItemBlock, ExecuteRequest
from theoriq.types import RequestBiscuit, ResponseBiscuit

agent_var: ContextVar[Agent] = ContextVar("agent")


def theoriq_blueprint(agent_config: AgentConfig, execute_fn: Callable[[list[DialogItem]], flask.Response]) -> Blueprint:
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
    json_body = request.json
    nonce: str = json_body["nonce"]
    nonce_bytes = bytes.fromhex(nonce)
    signature = agent_var.get().sign_challenge(nonce_bytes)
    return jsonify({"signature": signature.hex(), "nonce": nonce})


def execute(func: Callable[[list[DialogItem]], flask.Response]) -> flask.Response:
    """Execute endpoint"""
    agent = agent_var.get()
    req_biscuit = process_biscuit_request(agent, request)

    # TODO: Set biscuit as context var! (Maybe in something called theoriq.ExecuteRequest
    execute_request = ExecuteRequest.model_validate(request.json)
    response = func(execute_request.items)

    resp_biscuit = process_biscuit_response(agent, req_biscuit, response)
    response = add_biscuit_to_response(response, resp_biscuit)

    return response


def process_biscuit_request(agent: Agent, request: flask.Request) -> RequestBiscuit:
    try:
        bearer_token = get_bearer_token(request)
        print("Received", bearer_token)
        request_body = request.data
        print(request_body)
        return agent.parse_and_verify_biscuit(bearer_token, request_body)
    except (ParseBiscuitError, VerificationError) as err:
        raise flask.abort(401, err)


def process_biscuit_response(agent: Agent, req_biscuit: RequestBiscuit, response: flask.Response) -> ResponseBiscuit:
    resp_body = response.get_data()
    cost = TheoriqCost.zero("USDC")
    return agent.attenuate_biscuit_for_response(req_biscuit, resp_body, cost)


def get_bearer_token(request: flask.Request) -> str:
    """Get the bearer token from the request"""
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise VerificationError("Authorization header is missing")
    else:
        return authorization[len("bearer ") :]


def get_last_request(request_json: dict) -> str:
    """Retrieve the last request from the request"""
    items = request_json.get("items", [])
    last_item = items[-1]
    return last_item["items"][0]["data"]


def new_response(answer: int) -> DialogItem:
    return DialogItem(
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
        source="AwesomeSum",
        sourceType="Agent",
        items=[DialogItemBlock(type="text:markdown", data=str(answer))],
    )


def add_biscuit_to_response(response: flask.Response, resp_biscuit: ResponseBiscuit) -> flask.Response:
    response.headers.add("authorization", f"bearer {resp_biscuit.to_base64()}")
    return response
