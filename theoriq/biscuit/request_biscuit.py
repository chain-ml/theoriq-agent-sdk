from __future__ import annotations

import os
import uuid
from typing import Any, Dict
from uuid import UUID

from biscuit_auth import Biscuit, BlockBuilder, KeyPair  # pylint: disable=E0611
from biscuit_auth.biscuit_auth import PrivateKey, PublicKey  # type: ignore

from .agent_address import AgentAddress
from .facts import ExecuteRequestFacts, TheoriqRequest, TheoriqResponse
from .response_biscuit import ResponseBiscuit, ResponseFacts
from .theoriq_biscuit import TheoriqBiscuit
from .utils import from_base64_token


class RequestFacts:
    """Required facts inside the request biscuit"""

    def __init__(self, request_id: UUID | str, request: TheoriqRequest) -> None:
        self.req_id = request_id if isinstance(request_id, UUID) else UUID(request_id)
        self.request = request

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    @staticmethod
    def from_biscuit(biscuit: Biscuit) -> RequestFacts:
        """Read request facts from biscuit"""
        theoriq_biscuit = TheoriqBiscuit(biscuit)
        biscuit_facts = theoriq_biscuit.read_fact(ExecuteRequestFacts)
        request_id = biscuit_facts.request.request_id
        theoriq_request = TheoriqRequest.from_theoriq_fact(biscuit_facts.request)
        return RequestFacts(request_id, theoriq_request)

    @staticmethod
    def generate_new_biscuit(body: bytes, *, from_addr: str, to_addr: str) -> Biscuit:
        subject_address = AgentAddress(to_addr)
        request_facts = RequestFacts.default(body=body, from_addr=from_addr, to_addr=to_addr)

        tq_private_key = os.getenv("THEORIQ_PRIVATE_KEY", "")
        private_key = PrivateKey.from_hex(tq_private_key.removeprefix("0x"))

        authority_block_builder = subject_address.new_authority_builder()
        authority_block_builder.merge(request_facts.to_block_builder())
        return authority_block_builder.build(private_key)

    def to_block_builder(self) -> BlockBuilder:
        """Construct a biscuit block builder using the facts"""
        request_fact = self.request.to_theoriq_fact(self.req_id)

        block_builder = BlockBuilder("")
        block_builder.merge(request_fact.to_block_builder())
        return block_builder

    def __str__(self) -> str:
        return f"RequestFacts(req_id={self.req_id}, request={self.request})"

    @classmethod
    def default(cls, body: bytes, from_addr: str, to_addr: str) -> RequestFacts:
        theoriq_request = TheoriqRequest.from_body(body=body, from_addr=from_addr, to_addr=to_addr)
        return cls(uuid.uuid4(), theoriq_request)


class RequestBiscuit:
    """Request biscuit used by the `Theoriq` protocol"""

    def __init__(self, biscuit: Biscuit) -> None:
        self.biscuit: Biscuit = biscuit
        self.request_facts = RequestFacts.from_biscuit(biscuit)

    def attenuate_for_response(self, body: bytes, agent_private_key: PrivateKey) -> ResponseBiscuit:
        theoriq_response = TheoriqResponse.from_body(body, to_addr=self.request_facts.request.from_addr)
        response_facts = ResponseFacts(self.request_facts.req_id, theoriq_response)
        agent_kp = KeyPair.from_private_key(agent_private_key)
        attenuated_biscuit = self.biscuit.append_third_party_block(agent_kp, response_facts.to_block_builder())  # type: ignore

        return ResponseBiscuit(attenuated_biscuit, response_facts)

    def attenuate_for_request(
        self, request: TheoriqRequest, agent_private_key: PrivateKey, request_id: UUID | str
    ) -> RequestBiscuit:
        agent_kp = KeyPair.from_private_key(agent_private_key)
        request_facts = RequestFacts(request_id, request)
        attenuated_biscuit = self.biscuit.append_third_party_block(agent_kp, request_facts.to_block_builder())  # type: ignore
        return RequestBiscuit(attenuated_biscuit)

    def to_base64(self) -> str:
        return self.biscuit.to_base64()

    def to_headers(self) -> Dict[str, Any]:
        return {
            "Content-Type": "application/json",
            "Authorization": "bearer " + self.biscuit.to_base64(),
        }

    def __str__(self) -> str:
        return f"RequestBiscuit(biscuit={self.biscuit}, request_facts={self.request_facts})"

    @classmethod
    def from_token(cls, *, token: str, public_key: str) -> RequestBiscuit:
        public_key = public_key.removeprefix("0x")
        biscuit = from_base64_token(token, PublicKey.from_hex(public_key))
        return cls(biscuit)
