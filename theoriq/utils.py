"""Utility module"""

import os


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


def is_protocol_secured() -> bool:
    return os.getenv("THEORIQ_SECURED", "true").lower() == "true"
