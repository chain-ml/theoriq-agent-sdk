from typing import Tuple

from biscuit_auth import Biscuit, BiscuitValidationError, PublicKey  # pylint: disable=E0611
from biscuit_auth.biscuit_auth import KeyPair  # type: ignore
from sha3 import keccak_256  # type: ignore

from .error import ParseBiscuitError


def from_base64_token(token: str, public_key: PublicKey) -> Biscuit:
    try:
        return Biscuit.from_base64(token, public_key)
    except BiscuitValidationError as validation_err:
        raise ParseBiscuitError(f"fail to parse token {token[:3]}...") from validation_err


def hash_public_key(key: PublicKey) -> str:
    return keccak_256(key.to_hex().encode("utf-8")).hexdigest()


def get_new_key_pair() -> Tuple[str, str]:
    kp = KeyPair()
    return f"0x{kp.public_key.to_hex()}", f"0x{kp.private_key.to_hex()}"
