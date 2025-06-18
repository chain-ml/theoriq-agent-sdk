import os


def is_protocol_secured() -> bool:
    return os.getenv("THEORIQ_SECURED", "true").lower() == "true"
