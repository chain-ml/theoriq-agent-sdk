import uuid

from datetime import datetime, timedelta, timezone
from biscuit_auth import BiscuitBuilder, KeyPair, Check, Policy
from biscuit import *

# TODO: API
#   -> Authorize incoming biscuits
#       - Check the root public key comes from the backend
#       - Check the subject address is the same as the agent
#       - Check the expiration timestamp
#   -> Retrieve request facts from biscuit (they should be in the authority block)
#   -> Retrieve response facts from biscuit (they should be in the authority block)
#   -> Attenuate a biscuit with request facts (Add a third party block)
#   -> Attenuate a biscuit with response facts (Add a third party block)

# FIXME:
#   -> Maybe we should add a verification in the authorizer to check that subject.addr == theoriq:request.to_addr


def authorizer(subject_addr: str) -> Authorizer:
    """
    Build an authorizer object for Biscuit authorization.
    :param subject_addr: subject address of the receiver of the biscuit
    :return: Authorizer object
    """
    return with_subject_address_policy(
        with_expiration_check(Authorizer()), subject_addr
    )


def with_subject_address_policy(
    authorizer: Authorizer, subject_addr: str
) -> Authorizer:
    """
    Add a subject address policy to the given authorizer.

    :param authorizer: authorizer object
    :param subject_addr: subject_address string
    :return: authorizer object
    """
    policy = Policy(
        """allow if theoriq:subject("agent", {addr})""", {"addr": subject_addr}
    )
    authorizer.add_policy(policy)
    return authorizer


def with_expiration_check(authorizer: Authorizer) -> Authorizer:
    """
    Add an expiration check to the given authorizer.
    :param authorizer: authorizer object
    :return: authorizer object
    """

    now = datetime.now(tz=timezone.utc)
    print("now", int(now.timestamp()))
    check = Check(
        "check if theoriq:expires_at($time), $time > {now}",
        {"now": int(now.timestamp())},
    )
    authorizer.add_check(check)
    return authorizer


def authority_block(subject_addr: str, expires_at: datetime) -> BiscuitBuilder:
    return BiscuitBuilder(
        """
        theoriq:subject("agent", {subject_addr});
        theoriq:expires_at({expires_at});
        """,
        {"subject_addr": subject_addr, "expires_at": int(expires_at.timestamp())},
    )


if __name__ == "__main__":
    root_kp = KeyPair()

    # TEST for the authorization!
    # ===========================
    subject_address = "0x1234"
    expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=1)
    print(expires_at.timestamp())
    authority = authority_block(subject_address, expires_at)
    biscuit = authority.build(root_kp.private_key)

    print(biscuit.to_base64())

    authorizer = authorizer(subject_address)
    authorizer.add_token(biscuit)
    authorizer.authorize()
    # ===========================

    # # Attenuate for a response
    # theoriq_response = TheoriqResponse(body_hash="<hash_of_body>", to_addr="<target_addr>")
    # theoriq_cost = TheoriqCost(amount="10", currency="USDC")
    # response_facts = ResponseFacts(uuid.uuid4(), theoriq_response, theoriq_cost)
    #
    # external_kp = KeyPair()
    # third_party_block = response_facts.to_block()
    # biscuit = biscuit.append_third_party_block(external_kp, third_party_block)
    #
    # print(biscuit.to_base64())
    # print(biscuit)
