"""
subscribe.py

Types and functions used by an Agent when subscribing to a Theoriq agent
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable, List, Optional

from theoriq.agent import Agent
from theoriq.biscuit import RequestBiscuit, TheoriqBiscuit
from theoriq.utils import ControlledThread

from ..common import SubscribeContextBase
from .base_context import BaseContext
from .protocol.protocol_client import ProtocolClient
from .schemas.request import SubscribeRequestBody

# from theoriq.api.v1alpha2.protocol import ProtocolClient


class SubscribeContext(SubscribeContextBase, BaseContext):
    """
    Represents the context for subscribing to a Theoriq agent
    """

    def __init__(self, agent: Agent, protocol_client: ProtocolClient, timeout: int = 120) -> None:
        """
        Initializes a SubscribeContext instance.

        Args:
            agent (Agent): The agent subscribing to the channel.
            protocol_client (ProtocolClient): The client responsible for communicating with the protocol.
            request_biscuit (RequestBiscuit): The biscuit associated with the request, containing metadata and permissions.
        """
        authentication_biscuit = agent.authentication_biscuit(
            expires_at=datetime.now(tz=timezone.utc) + timedelta(seconds=timeout)
        )
        self._request_biscuit = RequestBiscuit.from_token(
            token=authentication_biscuit.to_base64(), public_key=protocol_client.public_key
        )
        SubscribeContextBase.__init__(self, agent, self._request_biscuit)
        BaseContext.__init__(self, agent, protocol_client, self._request_biscuit)

    def subscribe_to_agent_notifications(self, publisher_agent_id: str, handle_notification: Callable[[str], None]):
        theoriq_biscuit = TheoriqBiscuit(self._request_biscuit.biscuit)
        self._protocol_client.subscribe_to_agent_notifications(theoriq_biscuit, publisher_agent_id, handle_notification)


SubscribeListenerFn = Callable[[SubscribeContext, SubscribeRequestBody], None]
SubscribeListenerCleanupFn = Callable[[], None]
"""
Type alias for a function that takes an SubscribeContext and an SubscribeRequestBody,
and returns an None.
"""


class Subscriber:
    def __init__(self, id: str, target: Callable[[], None], cleanup_func: Optional[Callable[[], None]] = None):
        self.id = id
        self.subscriber_request_fn = target
        self.cleanup_func = cleanup_func

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

    @property
    def is_alive(self):
        return self.thread.is_alive()


class TheoriqSubscriptionManager:
    def __init__(self, agent: Agent):
        self.protocol_client = ProtocolClient.from_env()
        self.subscription_context = SubscribeContext(agent, self.protocol_client)
        self.listeners: List[Subscriber] = []

    def _subscribe(self, subscriber_request_fn: SubscribeListenerFn, publisher_agent_id: str) -> None:
        def _handle_notification(notification: str):
            # TODO: Handle configuration for the subscriber
            request_body = SubscribeRequestBody(
                configuration=None,
                message=notification,
            )
            subscriber_request_fn(self.subscription_context, request_body)

        self.subscription_context.subscribe_to_agent_notifications(publisher_agent_id, _handle_notification)

    def new_listener(
        self,
        subscriber_request_fn: SubscribeListenerFn,
        publisher_agent_id: str,
        cleanup_func: Optional[SubscribeListenerFn],
    ):
        def _subscribe():
            self._subscribe(subscriber_request_fn, publisher_agent_id)

        subscriber = Subscriber(
            id=publisher_agent_id,
            target=_subscribe,
            cleanup_func=self.cleanup_func(cleanup_func, publisher_agent_id),
        )
        self.listeners.append(subscriber)
        return subscriber

    def cleanup_func(self, cleanup_func: Optional[SubscribeListenerFn], publisher_agent_id: str) -> Callable[[], None]:
        def cleanup():
            self.listeners = [listener for listener in self.listeners if listener.id != publisher_agent_id]
            if cleanup_func:
                cleanup_func()

        return cleanup
