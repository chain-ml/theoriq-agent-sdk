import os
from typing import Callable, Optional, Type, TypeVar, overload


class MissingEnvVariableException(Exception):
    """
    Custom exception raised when a required environment variable is missing.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Missing required environment variable: {name}")


class EnvVariableValueException(Exception):
    """
    Custom exception raised if an environment variable is assigned a value
    that is inconsistent with its declared data type.
    """

    def __init__(self, name: str, value: str, expected_type: Type) -> None:
        self.name = name
        super().__init__(f"Environment variable {name} value `{value}` has invalid type, expected: {expected_type}")


T = TypeVar("T")


def _read_env_required(name: str, convert: Callable[[str], T]) -> T:
    result = os.getenv(name)
    if result is None:
        raise MissingEnvVariableException(name)
    return convert(result)


def _read_env_optional(name: str, default: Optional[T], convert: Callable[[str], T]) -> Optional[T]:
    result = os.getenv(name)
    if result is not None:
        return convert(result)
    return default


@overload
def read_env_str(name: str, *, required: bool = True) -> str: ...


@overload
def read_env_str(name: str, *, default: Optional[str] = None) -> Optional[str]: ...


def read_env_str(name: str, *, required: bool = False, default: Optional[str] = None) -> Optional[str]:
    """Read an environment variable as string."""
    if required:
        return _read_env_required(name, lambda x: x)
    return _read_env_optional(name, default, lambda x: x)


@overload
def read_env_int(name: str, *, required: bool = True) -> int: ...


@overload
def read_env_int(name: str, *, default: Optional[int] = None) -> Optional[int]: ...


def read_env_int(name: str, *, required: bool = False, default: Optional[int] = None) -> Optional[int]:
    """Read an environment variable as integer."""

    def converter(x: str) -> int:
        try:
            return int(x)
        except ValueError as e:
            raise EnvVariableValueException(name, x, int) from e

    if required:
        return _read_env_required(name, converter)
    return _read_env_optional(name, default, converter)


@overload
def read_env_float(name: str, *, required: bool = True) -> float: ...


@overload
def read_env_float(name: str, *, default: Optional[float] = None) -> Optional[float]: ...


def read_env_float(name: str, *, required: bool = False, default: Optional[float] = None) -> Optional[float]:
    """Read an environment variable as float."""

    def converter(x: str) -> float:
        try:
            return float(x)
        except ValueError as e:
            raise EnvVariableValueException(name, x, float) from e

    if required:
        return _read_env_required(name, converter)
    return _read_env_optional(name, default, converter)


@overload
def read_env_bool(name: str, *, required: bool = True) -> bool: ...


@overload
def read_env_bool(name: str, *, default: Optional[bool] = None) -> Optional[bool]: ...


def read_env_bool(name: str, *, required: bool = False, default: Optional[bool] = None) -> Optional[bool]:
    """Read an environment variable as boolean."""

    def converter(x: str) -> bool:
        result = x.strip().lower()
        if result in ["true", "1", "t"]:
            return True
        if result in ["false", "0", "f"]:
            return False
        raise EnvVariableValueException(name, x, bool)

    if required:
        return _read_env_required(name, converter)
    return _read_env_optional(name, default, converter)
