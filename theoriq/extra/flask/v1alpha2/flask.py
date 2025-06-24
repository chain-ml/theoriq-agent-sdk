"""Helpers to write agent using a flask web app."""

import json
import logging
import threading

import pydantic
from flask import Blueprint, Response, jsonify, request

import theoriq
from theoriq import ExecuteRuntimeError
from theoriq.api import ExecuteContextV1alpha2, ExecuteRequestFnV1alpha2
from theoriq.api.v1alpha2 import ConfigureContext
from theoriq.api.v1alpha2.agent import Agent, AgentDeploymentConfiguration
from theoriq.api.v1alpha2.configure import AgentConfigurator
from theoriq.api.v1alpha2.schemas import AgentSchemas, ExecuteRequestBody
from theoriq.biscuit import TheoriqBiscuit, TheoriqBiscuitError
from theoriq.extra.flask.common import get_bearer_token
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
    agent_config: AgentDeploymentConfiguration,
    execute_fn: ExecuteRequestFnV1alpha2,
    schemas: AgentSchemas = AgentSchemas.empty(),
    agent_configurator: AgentConfigurator = AgentConfigurator.default(),
) -> Blueprint:
    """
    Theoriq blueprint
    :return: a blueprint with all the routes required by the `theoriq` protocol
    """

    main_blueprint = Blueprint("main_blueprint", __name__)
    Agent.validate_schemas(schemas)

    @main_blueprint.before_request
    def set_context() -> None:
        agent_var.set(Agent(agent_config, schemas))

    configure_error_handlers(main_blueprint)

    v1alpha2_blueprint = _build_v1alpha2_blueprint(execute_fn, agent_configurator)
    main_blueprint.register_blueprint(v1alpha2_blueprint)
    return main_blueprint


def configure_error_handlers(main_blueprint: Blueprint) -> None:
    @main_blueprint.errorhandler(Exception)
    def handle_exception(e: Exception) -> Response:
        logging.exception(e)
        return build_error_payload(
            agent_address=str(agent_var.get().config.address), request_id="", err=str(e), status_code=500
        )

    @main_blueprint.errorhandler(TheoriqBiscuitError)
    def handle_biscuit_exception(e: TheoriqBiscuitError) -> Response:
        return build_error_payload(
            agent_address=str(agent_var.get().config.address), request_id="", err=str(e), status_code=401
        )


def theoriq_configuration_blueprint(agent_configurator: AgentConfigurator) -> Blueprint:
    blueprint = Blueprint("theoriq_configuration", __name__, url_prefix="/configuration")
    blueprint.add_url_rule("/schema", view_func=get_configuration_schema, methods=["GET"])
    blueprint.add_url_rule("/<string:agent_id>/validate", view_func=validate_configuration, methods=["POST"])
    blueprint.add_url_rule(
        "/<string:agent_id>/apply",
        view_func=lambda agent_id: apply_configuration(agent_id, agent_configurator),
        methods=["POST"],
    )
    return blueprint


def theoriq_schemas_blueprint() -> Blueprint:
    blueprint = Blueprint("theoriq_schemas", __name__, url_prefix="/schemas")
    blueprint.add_url_rule("/", view_func=get_schemas, methods=["GET"])
    return blueprint


def theoriq_execute_blueprint(execute_fn: ExecuteRequestFnV1alpha2) -> Blueprint:
    blueprint = Blueprint("theoriq_execute", __name__)
    blueprint.add_url_rule(
        "/execute", view_func=lambda: execute_v1alpha2(execute_fn), methods=["POST"], endpoint="execute"
    )
    blueprint.add_url_rule(
        "/execute-async",
        view_func=lambda: execute_async_v1alpha2(execute_fn),
        methods=["POST"],
        endpoint="execute-async",
    )

    return blueprint


def _build_v1alpha2_blueprint(execute_fn: ExecuteRequestFnV1alpha2, agent_configurator: AgentConfigurator) -> Blueprint:
    v1alpha2_blueprint = Blueprint("v1alpha2", __name__, url_prefix="/api/v1alpha2")
    v1alpha2_blueprint.register_blueprint(theoriq_execute_blueprint(execute_fn))
    v1alpha2_blueprint.register_blueprint(theoriq_system_blueprint())
    v1alpha2_blueprint.register_blueprint(theoriq_configuration_blueprint(agent_configurator))
    v1alpha2_blueprint.register_blueprint(theoriq_schemas_blueprint())

    return v1alpha2_blueprint


def execute_v1alpha2(execute_request_function: ExecuteRequestFnV1alpha2) -> Response:
    """Execute endpoint"""
    logger.debug("Executing request")
    agent = agent_var.get()
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
            response_biscuit = execute_context.new_response_biscuit(response.get_data())
            response = add_biscuit_to_response(response, response_biscuit)
            return response
        except pydantic.ValidationError as err:
            return new_error_response(execute_context, err, 400)
        except Exception as err:
            logger.exception(err)
            return new_error_response(execute_context, err, 500)


def execute_async_v1alpha2(execute_request_function: ExecuteRequestFnV1alpha2) -> Response:
    """Execute async endpoint"""
    logger.debug("Execute async request")
    agent = agent_var.get()
    protocol_client = theoriq.api.v1alpha2.ProtocolClient.from_env()
    request_biscuit = process_biscuit_request(agent, protocol_client.public_key, request)
    execute_context = ExecuteContextV1alpha2(agent, protocol_client, request_biscuit)
    with ExecuteLogContext(execute_context):
        try:
            execute_request_body = ExecuteRequestBody.model_validate(request.json)
            execute_context.set_configuration(execute_request_body.configuration)

            # Execute user's function
            thread = threading.Thread(
                target=_execute_async, args=(execute_request_function, execute_context, execute_request_body)
            )
            thread.start()
            return Response(status=202)

        except pydantic.ValidationError as err:
            return new_error_response(execute_context, err, 400)
        except Exception as err:
            logger.exception(err)
            return new_error_response(execute_context, err, 500)


def _execute_async(
    execute_fn: ExecuteRequestFnV1alpha2,
    execute_context: ExecuteContextV1alpha2,
    execute_request_body: ExecuteRequestBody,
) -> None:
    try:
        execute_response = execute_fn(execute_context, execute_request_body)
    except ExecuteRuntimeError as err:
        execute_response = execute_context.runtime_error_response(err)

    response_payload = {"response": execute_response.body.to_dict()}
    response = Response(response=json.dumps(response_payload), content_type="application/json")
    response_biscuit = execute_context.new_response_biscuit(response.get_data())

    execute_context.complete_request(response_biscuit, response.get_data())


def get_configuration_schema() -> Response:
    agent = agent_var.get()
    return jsonify(agent.schemas.configuration or {})


def get_schemas() -> Response:
    agent = agent_var.get()
    return jsonify(agent.schemas.model_dump())


def validate_configuration(agent_id: str) -> Response:
    payload = request.json
    agent = agent_var.get()
    agent.validate_configuration(payload)
    return Response(status=200)


def apply_configuration(agent_id: str, agent_configurator: AgentConfigurator) -> Response:
    payload = request.json  # <-- TODO: The payload should be fetched instead of relying on the one received.
    agent = agent_var.get()
    protocol_client = theoriq.api.v1alpha2.ProtocolClient.from_env()

    # Validate configuration
    agent.validate_configuration(payload)
    context = ConfigureContext(agent, protocol_client)
    context.set_virtual_address(agent_id)

    # Authorize biscuit
    token = get_bearer_token(request)
    theoriq_biscuit = TheoriqBiscuit.from_token(token=token, public_key=protocol_client.public_key)
    agent.authorize_biscuit(theoriq_biscuit.biscuit)

    if agent_configurator.is_long_running_fn(context, payload):
        thread = threading.Thread(target=agent_configurator, args=(context, payload, theoriq_biscuit, agent))
        thread.start()
        return Response(status=202)
    else:
        agent_configurator.configure_fn(context, payload)
        return Response(status=200)
