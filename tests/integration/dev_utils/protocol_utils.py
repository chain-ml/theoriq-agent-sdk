import os

import dotenv
import httpx

from theoriq.api.v1alpha2 import AgentResponse
from theoriq.types import AgentDataObject

dotenv.load_dotenv()

THEORIQ_URI = os.environ["THEORIQ_URI"]
BISCUIT = os.environ["BISCUIT"]


# TODO: what could be moved to ProtocolClient?


def register_agent(agent_data_obj: AgentDataObject) -> AgentResponse:
    url = f"{THEORIQ_URI}/api/v1alpha2/agents"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {BISCUIT}"}

    # TODO: fix AgentDataObject schema; provide to_payload()
    payload = {
        "configuration": {
            "deployment": {"headers": [{"name": "name", "value": "value"}], "url": agent_data_obj.spec.urls.end_point},
        },
        "metadata": {
            "name": agent_data_obj.spec.metadata.name,
            "shortDescription": agent_data_obj.spec.metadata.descriptions.short,
            "longDescription": agent_data_obj.spec.metadata.descriptions.long,
            "tags": agent_data_obj.spec.metadata.tags,
            "examplePrompts": agent_data_obj.spec.metadata.examples,
            "imageUrl": agent_data_obj.spec.urls.icon,
            "costCard": agent_data_obj.spec.metadata.cost_card,
        },
    }

    with httpx.Client() as client:
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return AgentResponse(**response.json())


def mint_agent(agent_id: str) -> None:
    url = f"{THEORIQ_URI}/api/v1alpha2/agents/{agent_id}/mint"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {BISCUIT}"}

    with httpx.Client() as client:
        response = client.post(url, headers=headers)
        response.raise_for_status()


def unmint_agent(agent_id: str) -> None:
    url = f"{THEORIQ_URI}/api/v1alpha2/agents/{agent_id}/unmint"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {BISCUIT}"}

    with httpx.Client() as client:
        response = client.post(url, headers=headers)
        response.raise_for_status()


def delete_agent(agent_id: str) -> None:
    url = f"{THEORIQ_URI}/api/v1alpha2/agents/{agent_id}"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {BISCUIT}"}

    with httpx.Client() as client:
        response = client.delete(url, headers=headers)
        response.raise_for_status()
