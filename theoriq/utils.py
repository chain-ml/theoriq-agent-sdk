"""Utility module"""

import hashlib


def hash_body(body: bytes) -> str:
    """Hash the given body using the sha256 algorithm"""
    return hashlib.sha256(body).hexdigest()
