import hashlib
from typing import Any, Self


class PayloadHash:
    def __init__(self, payload: bytes) -> None:
        """
        Initialize the PayloadHash with the given payload and compute its hash.
        """
        self.hash = self.compute_hash(payload)

    @staticmethod
    def compute_hash(payload: bytes) -> str:
        """
        Compute the SHA-256 hash of the given payload and return it as a hex string.
        """
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _normalize_hash(hash_str: str) -> str:
        """
        Normalize the hash by removing the '0x' prefix (if present) and converting to lowercase.
        """
        return hash_str.lower().removeprefix("0x")

    def __eq__(self, other: Any) -> bool:
        """
        Compare two PayloadHash objects or a PayloadHash object with a string.
        This comparison is case-insensitive and ignores the '0x' prefix.
        """
        if isinstance(other, PayloadHash):
            return self._normalize_hash(self.hash) == self._normalize_hash(other.hash)
        elif isinstance(other, str):
            return self._normalize_hash(self.hash) == self._normalize_hash(other)
        return False

    def __repr__(self) -> str:
        """
        Return the string representation of the PayloadHash object.
        """
        return f"PayloadHash(hash='0x{self.hash}')"

    def __str__(self) -> str:
        """
        Return the hash as a string in '0x' prefixed format.
        """
        return f"0x{self.hash}"

    @classmethod
    def from_str(cls, payload: str) -> Self:
        return cls(payload.encode("utf-8"))
