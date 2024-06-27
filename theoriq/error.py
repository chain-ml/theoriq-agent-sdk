"""Error returned by the theoriq SDK."""


class VerificationError(Exception):
    """Biscuit verification failure"""

    def __init__(self, message):
        super().__init__(message)


class ParseBiscuitError(Exception):
    """Biscuit parsing failure"""

    def __init__(self, message):
        super().__init__(message)
