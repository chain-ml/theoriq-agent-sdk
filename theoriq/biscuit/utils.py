from typing import Tuple

from biscuit_auth import Biscuit, BiscuitValidationError, KeyPair, PublicKey  # pylint: disable=E0611
from sha3 import keccak_256  # type: ignore

from .error import ParseBiscuitError


def from_base64_token(token: str, public_key: PublicKey) -> Biscuit:
    try:
        return Biscuit.from_base64(token, public_key)
    except BiscuitValidationError as validation_err:
        raise ParseBiscuitError(f"fail to parse token {token[:3]}...") from validation_err


def hash_public_key(key: PublicKey) -> str:
    return keccak_256(bytes.fromhex(key.to_hex())).hexdigest()


def get_new_key_pair() -> Tuple[str, str]:
    kp = KeyPair()
    return f"0x{kp.public_key.to_hex()}", f"0x{kp.private_key.to_hex()}"


def verify_address(address: str) -> str:
    """
    Verify the address
    :raise TypeError: if the address is not 32 bytes long or does not only contain hex digits
    """
    add = address.removeprefix("0x").strip()
    try:
        length = len(bytes.fromhex(add))
        if length != 32:
            raise TypeError(f"address must be 32 bytes long: {address}")
    except ValueError as e:
        raise TypeError(f"address must only contain hex digits: {address}") from e
    else:
        return add
