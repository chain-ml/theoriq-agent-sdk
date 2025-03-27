from theoriq.api.v1alpha2.protocol.protocol_client import ProtocolClient
import logging
import threading
from typing import Callable
import time
from theoriq.biscuit import TheoriqBiscuit

logger = logging.getLogger(__name__)

def theoriq_subscribe_to_agent(agent_id: str, subscribe_fn: Callable[[str], None], access_token: str):
    """
    Subscribe to an agent
    """
    def _subscribe():
        protocol_client = ProtocolClient.from_env()
        biscuit = TheoriqBiscuit.from_token(token=access_token, public_key=protocol_client.public_key)
        while True:
            for message in protocol_client.subscribe_to_agent_notifications(biscuit, agent_id):
                subscribe_fn(message)
            time.sleep(1) # wait for 1 second before reconnecting
    return threading.Thread(target=_subscribe)
   