from biscuit_auth import Biscuit, BiscuitValidationError, PublicKey  # pylint: disable=E0611
from sha3 import keccak_256  # type: ignore

from .error import ParseBiscuitError


def from_base64_token(token: str, public_key: PublicKey) -> Biscuit:
    try:
        return Biscuit.from_base64(token, public_key)
    except BiscuitValidationError as validation_err:
        raise ParseBiscuitError(f"fail to parse token {token[:3]}...") from validation_err


def hash_public_key(key: PublicKey) -> str:
    return keccak_256(bytes.fromhex(key.to_hex())).hexdigest()
