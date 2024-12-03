"""Helpers to write agent using a flask web app."""

import logging

import pydantic
from flask import Blueprint, Response, jsonify, request

import theoriq
from theoriq import ExecuteRuntimeError
from theoriq.agent import Agent, AgentDeploymentConfiguration
from theoriq.api import ExecuteContextV1alpha1, ExecuteRequestFnV1alpha1
from theoriq.api.v1alpha1.schemas import ExecuteRequestBody as ExecuteRequestBodyV1
from theoriq.biscuit import TheoriqBiscuitError
from theoriq.extra.globals import agent_var

from ...logging.execute_context import ExecuteLogContext
from ..common import (
    add_biscuit_to_response,
    build_error_payload,
    new_error_response,
    process_biscuit_request,
    theoriq_system_blueprint,
)

logger = logging.getLogger(__name__)


def theoriq_blueprint(agent_config: AgentDeploymentConfiguration, execute_fn: ExecuteRequestFnV1alpha1) -> Blueprint:
    """
    Theoriq blueprint
    :return: a blueprint with all the routes required by the `theoriq` protocol
    """

    main_blueprint = Blueprint("main_blueprint", __name__)

    @main_blueprint.before_request
    def set_context():
        agent_var.set(Agent(agent_config, None))

    v1alpha1_blue_print = _build_v1alpha1_blueprint(execute_fn)
    main_blueprint.register_blueprint(v1alpha1_blue_print)

    return main_blueprint


def _build_v1alpha1_blueprint(execute_fn: ExecuteRequestFnV1alpha1) -> Blueprint:
    v1alpha1_blue_print = Blueprint("v1alpha1", __name__, url_prefix="/api/v1alpha1")
    v1alpha1_blue_print.add_url_rule("/execute", view_func=lambda: execute_v1alpha1(execute_fn), methods=["POST"])
    v1alpha1_blue_print.register_blueprint(theoriq_system_blueprint())
    return v1alpha1_blue_print


def execute_v1alpha1(execute_request_function: ExecuteRequestFnV1alpha1) -> Response:
    """Execute endpoint"""
    logger.debug("Executing request")
    agent = agent_var.get()
    try:
        protocol_client = theoriq.api.v1alpha1.ProtocolClient.from_env()
        request_biscuit = process_biscuit_request(agent, protocol_client.public_key, request)
        execute_context = ExecuteContextV1alpha1(agent, protocol_client, request_biscuit)
        with ExecuteLogContext(execute_context):
            try:
                # Execute user's function
                execute_request_body = ExecuteRequestBodyV1.model_validate(request.json)
                try:
                    execute_response = execute_request_function(execute_context, execute_request_body)
                except ExecuteRuntimeError as err:
                    execute_response = execute_context.runtime_error_response(err)

                response = jsonify(execute_response.body.to_dict())
                response_biscuit = execute_context.new_response_biscuit(
                    response.get_data(), execute_response.theoriq_cost
                )
                response = add_biscuit_to_response(response, response_biscuit)
            except pydantic.ValidationError as err:
                response = new_error_response(execute_context, err, 400)
            except Exception as err:
                logger.exception(err)
                response = new_error_response(execute_context, err, 500)
    except TheoriqBiscuitError as err:
        # Process the request biscuit. If not present, return a 401 error
        return build_error_payload(
            agent_address=str(agent.config.address), request_id="", err=str(err), status_code=401
        )
    except Exception as err:
        return build_error_payload(
            agent_address=str(agent.config.address), request_id="", err=str(err), status_code=500
        )
    else:
        return response
