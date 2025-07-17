from __future__ import annotations

from enum import Enum
from typing import Any


class SourceType(Enum):
    """
    An enumeration that defines two possible source types: 'User' and 'Agent'.
    This is used to categorize the source of certain actions or data.
    """

    User = "user"
    Agent = "agent"

    @staticmethod
    def from_value(value: Any) -> SourceType:
        """
        A static method that attempts to convert a given value to a `SourceType` enum.

        Parameters:
        value (Any): The value to be converted to a `SourceType`. This value is
                     expected to be a string matching either "user" or "agent".

        Returns:
        SourceType: The corresponding `SourceType` enum member if the value is valid.

        Raises:
        ValueError: If the provided value does not correspond to any of the `SourceType` enum members.
        """
        try:
            return SourceType(str(value).lower())
        except ValueError as e:
            raise ValueError(f"'{value}' is not a valid SourceType") from e

    @staticmethod
    def from_address(address: str) -> SourceType:
        """
        A static method that attempts to convert a given address to a `SourceType` enum.
        """

        length = len(address.removeprefix("0x"))
        if length == 40:
            return SourceType.User
        if length == 64:
            return SourceType.Agent
        raise ValueError(f"'{address}' is not a valid address")

    @property
    def is_user(self) -> bool:
        return self == SourceType.User

    @property
    def is_agent(self) -> bool:
        return self == SourceType.Agent

    def __str__(self) -> str:
        return str(self.value)
