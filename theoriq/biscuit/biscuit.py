"""
Helpers to work with biscuit data.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from biscuit_auth import Authorizer, Biscuit, BiscuitBuilder, Check, KeyPair, Policy, Rule
from theoriq.types import AgentAddress

from .facts import RequestFacts, ResponseFacts


def new_authority_block(subject_addr: str, expires_at: Optional[datetime] = None) -> BiscuitBuilder:
    """Creates a new authority block builder."""
    expires_at = expires_at or datetime.now(tz=timezone.utc) + timedelta(days=365)
    expiration_timestamp = int(expires_at.timestamp())
    return BiscuitBuilder(
        """
        theoriq:subject("agent", {subject_addr});
        theoriq:expires_at({expires_at});
        """,
        {"subject_addr": str(subject_addr), "expires_at": expiration_timestamp},
    )


def get_subject_address(biscuit: Biscuit) -> AgentAddress:
    """Get the subject address of a biscuit."""
    rule = Rule("""address($address) <- theoriq:subject("agent", $address)""")
    authorizer = _biscuit_authorizer(biscuit)
    facts = authorizer.query(rule)
    return AgentAddress(facts[0].terms[0])


def default_authorizer(agent_addr: AgentAddress) -> Authorizer:
    """
    Build an authorizer object for Biscuit authorization.
    :param agent_addr: subject address of the receiver of the biscuit
    :return: Authorizer object
    """
    authorizer = Authorizer()

    # Add subject address policy
    subject_addr_policy = Policy("""allow if theoriq:subject("agent", {addr})""", {"addr": str(agent_addr)})
    authorizer.add_policy(subject_addr_policy)

    # Add expiration check
    now = int(datetime.now(timezone.utc).timestamp())
    expiration_check = Check("check if theoriq:expires_at($time), $time > {now}", {"now": now})
    authorizer.add_check(expiration_check)

    return authorizer


def attenuate_for_request(biscuit: Biscuit, req_facts: RequestFacts, external_kp: KeyPair) -> Biscuit:
    """Attenuate a biscuit with the given request facts by appending a third party block"""
    return biscuit.append_third_party_block(external_kp, req_facts.to_block_builder())  # type: ignore


def attenuate_for_response(biscuit: Biscuit, resp_facts: ResponseFacts, external_kp: KeyPair) -> Biscuit:
    """Attenuate a biscuit with the given response facts by appending a third party block"""
    return biscuit.append_third_party_block(external_kp, resp_facts.to_block_builder())  # type: ignore


def _biscuit_authorizer(biscuit: Biscuit) -> Authorizer:
    """Get the authorizer of a biscuit."""
    authorizer = Authorizer()
    authorizer.add_token(biscuit)
    return authorizer
