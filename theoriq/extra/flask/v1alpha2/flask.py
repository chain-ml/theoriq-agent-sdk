"""Helpers to write agent using a flask web app."""

import logging
from typing import Dict, Optional

import pydantic
from flask import Blueprint, Response, jsonify, request

import theoriq
from theoriq import ExecuteRuntimeError
from theoriq.agent import Agent, AgentDeploymentConfiguration
from theoriq.api import ExecuteContextV1alpha2, ExecuteRequestFnV1alpha2
from theoriq.api.v1alpha2 import ConfigureContext, ConfigureFn
from theoriq.api.v1alpha2.schemas import ExecuteRequestBody
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


def theoriq_blueprint(
    agent_config: AgentDeploymentConfiguration, execute_fn: ExecuteRequestFnV1alpha2, schema: Optional[Dict] = None, configure_fn: Optional[ConfigureFn] = None
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

    v1alpha2_blueprint = _build_v1alpha2_blueprint(execute_fn, configure_fn)
    main_blueprint.register_blueprint(v1alpha2_blueprint)
    return main_blueprint


def theoriq_configuration_blueprint(configure_fn: Optional[ConfigureFn]) -> Blueprint:
    blueprint = Blueprint("theoriq_configuration", __name__, url_prefix="/configuration")
    blueprint.add_url_rule("/schema", view_func=get_configuration_schema, methods=["GET"])
    blueprint.add_url_rule("/<string:agent_id>/validate", view_func=validate_configuration, methods=["POST"])
    blueprint.add_url_rule("/<string:agent_id>/apply", view_func=lambda agent_id: apply_configuration(agent_id, configure_fn), methods=["POST"])
    return blueprint


def _build_v1alpha2_blueprint(execute_fn: ExecuteRequestFnV1alpha2, configure_fn: Optional[ConfigureFn] = None) -> Blueprint:
    v1alpha2_blueprint = Blueprint("v1alpha2", __name__, url_prefix="/api/v1alpha2")
    v1alpha2_blueprint.add_url_rule("/execute", view_func=lambda: execute_v1alpha2(execute_fn), methods=["POST"])
    v1alpha2_blueprint.register_blueprint(theoriq_system_blueprint())
    v1alpha2_blueprint.register_blueprint(theoriq_configuration_blueprint(configure_fn))

    return v1alpha2_blueprint


def execute_v1alpha2(execute_request_function: ExecuteRequestFnV1alpha2) -> Response:
    """Execute endpoint"""
    logger.debug("Executing request")
    agent = agent_var.get()
    try:
        protocol_client = theoriq.api.v1alpha2.ProtocolClient.from_env()
        request_biscuit = process_biscuit_request(agent, protocol_client.public_key, request)
        execute_context = ExecuteContextV1alpha2(agent, protocol_client, request_biscuit)
        with ExecuteLogContext(execute_context):
            try:
                execute_request_body = ExecuteRequestBody.model_validate(request.json)
                execute_context.set_configuration(execute_request_body.configuration)
                # Execute user's function
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


def get_configuration_schema() -> Response:
    agent = agent_var.get()
    return jsonify(agent.schema or {})


def validate_configuration(agent_id: str) -> Response:
    payload = request.json
    agent = agent_var.get()
    try:
        agent.validate_configuration(payload)
        return Response(status=200)
    except Exception as err:
        return build_error_payload(
            agent_address=str(agent.config.address), request_id="", err=str(err), status_code=401
        )


def apply_configuration(agent_id: str, configure_fn: Optional[ConfigureFn]) -> Response:
    payload = request.json
    agent = agent_var.get()
    try:
        agent.validate_configuration(payload)
        protocol_client = theoriq.api.v1alpha2.ProtocolClient.from_env()
        context = ConfigureContext(agent, protocol_client)
        context.set_virtual_address(agent_id)
        if configure_fn:
            configure_fn(context, payload)
        return Response(status=200)
    except Exception as err:
        return build_error_payload(
            agent_address=str(agent.config.address), request_id="", err=str(err), status_code=401
        )
