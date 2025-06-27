from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class AgentWeb3Transaction(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    agent_id: str
    chain_id: int
    hash: str
    metadata: Optional[Dict[str, str]] = None
    signer: str
    submitted_at: str
