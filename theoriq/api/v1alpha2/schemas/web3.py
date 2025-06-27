from typing import Dict, Optional

from pydantic import BaseModel, Field


class AgentWeb3Transaction(BaseModel):
    agent_id: str = Field(..., alias="agentId")
    chain_id: int = Field(..., alias="chainId")
    hash: str
    metadata: Optional[Dict[str, str]] = None
    signer: str
    submitted_at: str = Field(..., alias="submittedAt")


class AgentWeb3TransactionHash(BaseModel):
    tx_hash: str = Field(..., alias="txHash")
