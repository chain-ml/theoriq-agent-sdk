"""
error.py

Errors returned by the theoriq SDK
"""


class VerificationError(Exception):
    """Biscuit verification failure"""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ParseBiscuitError(Exception):
    """Biscuit parsing failure"""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
