"""
error.py

Errors returned by the Theoriq SDK
"""


class TheoriqBiscuitError(Exception):
    """Biscuit failure"""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class VerificationError(TheoriqBiscuitError):
    """Biscuit verification failure"""

    def __init__(self, message: str) -> None:
        super().__init__(f"Verification error: {message}")


class AuthorizationError(TheoriqBiscuitError):
    """Biscuit authorization failure"""

    def __init__(self, message: str) -> None:
        super().__init__(f"Authorization error: {message}")


class ParseBiscuitError(TheoriqBiscuitError):
    """Biscuit parsing failure"""

    def __init__(self, message: str) -> None:
        super().__init__(f"Parsing error: {message}")
