import hashlib
import re
from typing import Any, ClassVar, Self


class PayloadHash:
    _SHA256_REGEX: ClassVar[re.Pattern] = re.compile(r"^[a-fA-F0-9]{64}$")

    def __init__(self, payload: bytes) -> None:
        """
        Initialize the PayloadHash with the given payload and compute its hash.
        """
        self._hash = self.compute_hash(payload)

    @staticmethod
    def compute_hash(payload: bytes) -> str:
        """
        Compute the SHA-256 hash of the given payload and return it as a hex string.
        """
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _normalize_hash(hash_value: str) -> str:
        """
        Normalize the hash by removing the '0x' prefix (if present) and converting to lowercase.
        """
        return hash_value.lower().removeprefix("0x")

    def __eq__(self, other: Any) -> bool:
        """
        Compare two PayloadHash objects or a PayloadHash object with a string.
        This comparison is case-insensitive and ignores the '0x' prefix.
        """
        if isinstance(other, PayloadHash):
            return self._normalize_hash(self._hash) == self._normalize_hash(other._hash)
        elif isinstance(other, str):
            return self._normalize_hash(self._hash) == self._normalize_hash(other)
        return False

    def __repr__(self) -> str:
        """
        Return the string representation of the PayloadHash object.
        """
        return f"PayloadHash(hash='0x{self._hash}')"

    def __str__(self) -> str:
        """
        Return the hash as a string in '0x' prefixed format.
        """
        return f"0x{self._hash}"

    @classmethod
    def from_str(cls, payload: str) -> Self:
        return cls(payload.encode("utf-8"))

    @classmethod
    def from_hash(cls, hash_value: str) -> Self:
        result = cls(b"")
        tmp = cls._normalize_hash(hash_value)
        if not bool(cls._SHA256_REGEX.fullmatch(tmp)):
            raise ValueError(f"Hash value '{tmp}' is not a hex string")
        result._hash = tmp
        return result
