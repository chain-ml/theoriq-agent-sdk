"""
subscribe.py

Types and functions used by an Agent when subscribing to a Theoriq agent
"""

from __future__ import annotations

from typing import Callable, List, Optional

from theoriq.agent import Agent
from theoriq.biscuit import TheoriqBiscuit
from theoriq.utils import ControlledThread

from ..common import SubscribeContextBase
from .base_context import BaseContext
from .protocol.protocol_client import ProtocolClient
from .schemas.request import SubscribeRequestBody
import json

class SubscribeContext(SubscribeContextBase, BaseContext):
    """
    Represents the context for subscribing to a Theoriq agent
    """

    def __init__(self, agent: Agent, protocol_client: ProtocolClient) -> None:
        """
        Initializes a SubscribeContext instance.

        Args:
            agent (Agent): The agent subscribing to the channel.
            protocol_client (ProtocolClient): The client responsible for communicating with the protocol.
            request_biscuit (RequestBiscuit): The biscuit associated with the request, containing metadata and permissions.
        """
        SubscribeContextBase.__init__(self, agent)
        BaseContext.__init__(self, agent, protocol_client)

    def subscribe_to_agent_notifications(self, publisher_agent_id: str, handle_notification: Callable[[str], None]):
        response_biscuit = self.get_response_biscuit()
        protocol_public_key = self._protocol_client.public_key
        theoriq_biscuit = TheoriqBiscuit.from_token(token=response_biscuit.biscuit, public_key=protocol_public_key)
        self._protocol_client.subscribe_to_agent_notifications(theoriq_biscuit, publisher_agent_id, handle_notification)


SubscribeListenerFn = Callable[[SubscribeContext, SubscribeRequestBody], None]
SubscribeListenerCleanupFn = Callable[[SubscribeContext], None]
"""
Type alias for a function that takes an SubscribeContext and an SubscribeRequestBody,
and returns an None.
"""


class Subscriber:
    def __init__(
        self, subscriber_id: str, target: Callable[[], None], cleanup_func: Optional[Callable[[], None]] = None
    ):
        self.subscriber_id = subscriber_id
        self.subscriber_request_fn = target
        self.cleanup_func = cleanup_func
        self.thread: Optional[ControlledThread] = None

    def start_listener(self):
        self.thread = ControlledThread(
            target=self.subscriber_request_fn,
            cleanup_func=self.cleanup_func,
        )
        self.thread.start()

    def stop_listener(self):
        self.thread.kill()

    def join_listener(self):
        self.thread.join()

    def __repr__(self):
        return f"Subscriber(subscriber_id={self.subscriber_id}, thread={self.thread}, is_alive={self.is_alive})"

    @property
    def is_alive(self):
        try:
            return self.thread.is_alive()
        except Exception:
            return False


class TheoriqSubscriptionManager:
    def __init__(self, agent: Agent):
        self.protocol_client = ProtocolClient.from_env()
        self.agent = agent
        self.listeners: List[Subscriber] = []
        self.subscription_context: Optional[SubscribeContext] = None

    def _subscribe(self, subscriber_request_fn: SubscribeListenerFn, publisher_agent_id: str, is_json: bool) -> None:
        if not self.subscription_context:
            raise RuntimeError("Subscription context not set")

        def _handle_notification(notification: str):
            if not self.subscription_context:
                raise RuntimeError("Subscription context not set")

            if notification.strip() == ":":
                return #Keep-alive notification

            received_message = notification[6:] if notification.startswith("data: ") else notification
            processed_message = json.loads(received_message) if is_json else received_message
            # TODO: Handle configuration for the subscriber
            request_body = SubscribeRequestBody(
                configuration=None,
                message=processed_message,
            )
            subscriber_request_fn(self.subscription_context, request_body)

        self.subscription_context.subscribe_to_agent_notifications(publisher_agent_id, _handle_notification)

    def new_listener(
        self,
        subscriber_request_fn: SubscribeListenerFn,
        publisher_agent_id: str,
        cleanup_func: Optional[SubscribeListenerFn] = None,
        is_json: bool = False,
    ):
        self.subscription_context = SubscribeContext(self.agent, self.protocol_client)            
        subscriber = Subscriber(
            subscriber_id=publisher_agent_id,
            target=lambda: self._subscribe(subscriber_request_fn, publisher_agent_id, is_json),
            cleanup_func=self.cleanup_func(cleanup_func, publisher_agent_id),
        )
        self.listeners.append(subscriber)
        return subscriber

    def cleanup_func(self, cleanup_func: Optional[SubscribeListenerFn], publisher_agent_id: str) -> Callable[[], None]:
        def cleanup():
            self.listeners = [listener for listener in self.listeners if listener.subscriber_id != publisher_agent_id]
            if cleanup_func:
                cleanup_func(self.subscription_context)

        return cleanup
