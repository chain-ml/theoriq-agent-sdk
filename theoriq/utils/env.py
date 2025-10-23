import os
from decimal import Decimal, InvalidOperation
from typing import Callable, Optional, Type, TypeVar


class MissingEnvVariableException(Exception):
    """Required environment variable is missing."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Missing required environment variable: {name}")


class EnvVariableValueException(Exception):
    """Environment variable is assigned a value that is inconsistent with its declared data type."""

    def __init__(self, *, name: str, value: str, expected_type: Type) -> None:
        self.name = name
        super().__init__(f"Environment variable {name} value `{value}` has invalid type, expected: {expected_type}")


T = TypeVar("T")


def _read_env_required(name: str, convert: Callable[[str], T]) -> T:
    value = os.getenv(name)
    if value is not None:
        return convert(value)
    raise MissingEnvVariableException(name)


def _read_env_optional(name: str, default: Optional[T], convert: Callable[[str], T]) -> Optional[T]:
    value = os.getenv(name)
    if value is not None:
        return convert(value)
    return default


def _int_converter(name: str) -> Callable[[str], int]:
    def convert(x: str) -> int:
        try:
            return int(x)
        except ValueError as e:
            raise EnvVariableValueException(name=name, value=x, expected_type=int) from e

    return convert


def _float_converter(name: str) -> Callable[[str], float]:
    def convert(x: str) -> float:
        try:
            return float(x)
        except ValueError as e:
            raise EnvVariableValueException(name=name, value=x, expected_type=float) from e

    return convert


def _bool_converter(name: str) -> Callable[[str], bool]:
    def convert(x: str) -> bool:
        if x.lower() in ["true", "1", "t"]:
            return True
        if x.lower() in ["false", "0", "f"]:
            return False
        raise EnvVariableValueException(name=name, value=x, expected_type=bool)

    return convert


def _decimal_converter(name: str) -> Callable[[str], Decimal]:
    def convert(x: str) -> Decimal:
        try:
            return Decimal(x)
        except InvalidOperation as e:
            raise EnvVariableValueException(name=name, value=x, expected_type=Decimal) from e

    return convert


def read_env_str(name: str, default: Optional[str] = None) -> Optional[str]:
    """Read an environment variable as optional string."""
    return _read_env_optional(name, default, lambda x: x)


def must_read_env_str(name: str) -> str:
    """Read an environment variable as string."""
    return _read_env_required(name, lambda x: x)


def read_env_int(name: str, default: Optional[int] = None) -> Optional[int]:
    """Read an environment variable as optional integer."""
    return _read_env_optional(name, default, _int_converter(name))


def must_read_env_int(name: str) -> int:
    """Read an environment variable as integer."""
    return _read_env_required(name, _int_converter(name))


def read_env_float(name: str, default: Optional[float] = None) -> Optional[float]:
    """Read an environment variable as optional float."""
    return _read_env_optional(name, default, _float_converter(name))


def must_read_env_float(name: str) -> float:
    """Read an environment variable as float."""
    return _read_env_required(name, _float_converter(name))


def read_env_bool(name: str, default: Optional[bool] = None) -> Optional[bool]:
    """Read an environment variable as optional boolean."""
    return _read_env_optional(name, default, _bool_converter(name))


def must_read_env_bool(name: str) -> bool:
    """Read an environment variable as boolean."""
    return _read_env_required(name, _bool_converter(name))


def read_env_decimal(name: str, default: Optional[Decimal] = None) -> Optional[Decimal]:
    """Read an environment variable as optional decimal."""
    return _read_env_optional(name, default, _decimal_converter(name))


def must_read_env_decimal(name: str) -> Decimal:
    """Read an environment variable as decimal."""
    return _read_env_required(name, _decimal_converter(name))
