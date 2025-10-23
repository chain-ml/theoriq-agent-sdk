from decimal import Decimal

import pytest
from tests import OsEnviron

from theoriq.utils import (
    EnvVariableValueException,
    MissingEnvVariableException,
    must_read_env_bool,
    must_read_env_decimal,
    must_read_env_float,
    must_read_env_int,
    must_read_env_str,
    read_env_bool,
    read_env_decimal,
    read_env_float,
    read_env_int,
    read_env_str,
)


def test_must_read_env_str() -> None:
    with OsEnviron(name="STR", value="VALUE"):
        value = must_read_env_str("STR")
        assert isinstance(value, str)
        assert value == "VALUE"


def test_must_read_env_int() -> None:
    with OsEnviron(name="INT", value="2"):
        value = must_read_env_int("INT")
        assert isinstance(value, int)
        assert value == 2


def test_must_read_env_float() -> None:
    with OsEnviron(name="FLOAT", value="1.23456"):
        value = must_read_env_float("FLOAT")
        assert isinstance(value, float)
        assert value == 1.23456


def test_must_read_env_bool() -> None:
    with OsEnviron(name="T_BOOL", value="True"):
        value = must_read_env_bool("T_BOOL")
        assert isinstance(value, bool)
        assert value

    with OsEnviron(name="F_BOOL", value="False"):
        value = must_read_env_bool("F_BOOL")
        assert isinstance(value, bool)
        assert not value


def test_must_read_env_decimal() -> None:
    with OsEnviron(name="DECIMAL", value="1.23456"):
        value = must_read_env_decimal("DECIMAL")
        assert isinstance(value, Decimal)
        assert value == Decimal("1.23456")


def test_read_env_with_default() -> None:
    str_value = read_env_str("MISSING", default="DEFAULT")
    assert isinstance(str_value, str)
    assert str_value == "DEFAULT"

    int_value = read_env_int("MISSING", default=2)
    assert isinstance(int_value, int)
    assert int_value == 2

    float_value = read_env_float("MISSING", default=1.23456)
    assert isinstance(float_value, float)
    assert float_value == 1.23456

    bool_value = read_env_bool("MISSING", default=False)
    assert isinstance(bool_value, bool)
    assert not bool_value

    decimal_value = read_env_decimal("MISSING", default=Decimal("1.23456"))
    assert isinstance(decimal_value, Decimal)
    assert decimal_value == Decimal("1.23456")


def test_missing_env() -> None:
    str_value = read_env_str("MISSING")
    assert str_value is None

    int_value = read_env_int("MISSING")
    assert int_value is None

    float_value = read_env_float("MISSING")
    assert float_value is None

    bool_value = read_env_bool("MISSING")
    assert bool_value is None

    decimal_value = read_env_decimal("MISSING")
    assert decimal_value is None

    with pytest.raises(MissingEnvVariableException):
        must_read_env_str("MISSING")

    with pytest.raises(MissingEnvVariableException):
        must_read_env_int("MISSING")

    with pytest.raises(MissingEnvVariableException):
        must_read_env_float("MISSING")

    with pytest.raises(MissingEnvVariableException):
        must_read_env_bool("MISSING")

    with pytest.raises(MissingEnvVariableException):
        must_read_env_decimal("MISSING")


def test_invalid_env() -> None:
    with OsEnviron(name="INVALID_INT", value="NOT_AN_INT"):
        with pytest.raises(EnvVariableValueException):
            read_env_int("INVALID_INT")

    with OsEnviron(name="INVALID_FLOAT", value="2Gb"):
        with pytest.raises(EnvVariableValueException):
            read_env_float("INVALID_FLOAT")

    with OsEnviron(name="INVALID_BOOL", value="Tue"):
        with pytest.raises(EnvVariableValueException):
            must_read_env_bool("INVALID_BOOL")

    with OsEnviron(name="INVALID_DECIMAL", value="twenty_four"):
        with pytest.raises(EnvVariableValueException):
            must_read_env_decimal("INVALID_DECIMAL")
