import pytest

import main
from datetime import datetime, timezone, timedelta

from biscuit_auth import KeyPair, BiscuitBuilder, AuthorizationError


def test_authorization():
    root_kp = KeyPair()

    subject_address = "0x1234"
    expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=1)
    print(expires_at.timestamp())
    authority = new_authority_block(subject_address, expires_at)
    biscuit = authority.build(root_kp.private_key)

    authorizer = main.authorizer(subject_address)
    authorizer.add_token(biscuit)
    authorizer.authorize()


def test_authorization_expired():
    root_kp = KeyPair()

    subject_address = "0x1234"
    expires_at = datetime.now(tz=timezone.utc) - timedelta(hours=1)
    print(expires_at.timestamp())
    authority = new_authority_block(subject_address, expires_at)
    biscuit = authority.build(root_kp.private_key)

    authorizer = main.authorizer(subject_address)
    authorizer.add_token(biscuit)
    with pytest.raises(AuthorizationError):
        authorizer.authorize()


def test_authorization_wrong_subject_address():
    root_kp = KeyPair()

    subject_address = "0x1234"
    expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=1)
    print(expires_at.timestamp())
    authority = new_authority_block(subject_address, expires_at)
    biscuit = authority.build(root_kp.private_key)

    authorizer = main.authorizer("0x12345")
    authorizer.add_token(biscuit)
    with pytest.raises(AuthorizationError):
        authorizer.authorize()


def new_authority_block(subject_addr: str, expires_at: datetime) -> BiscuitBuilder:
    return BiscuitBuilder(
        """
        theoriq:subject("agent", {subject_addr});
        theoriq:expires_at({expires_at});
        """,
        {"subject_addr": subject_addr, "expires_at": int(expires_at.timestamp())},
    )

