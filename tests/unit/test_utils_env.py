import os

import pytest

from theoriq.utils import (
    EnvVariableValueException,
    MissingEnvVariableException,
    must_read_env_bool,
    must_read_env_float,
    must_read_env_int,
    must_read_env_str,
    read_env_bool,
    read_env_float,
    read_env_int,
    read_env_str,
)


def test_must_read_env_str() -> None:
    os.environ["STR"] = "VALUE"
    value = must_read_env_str("STR")
    assert isinstance(value, str)
    assert value == "VALUE"


def test_must_read_env_int() -> None:
    os.environ["INT"] = "2"
    value = must_read_env_int("INT")
    assert isinstance(value, int)
    assert value == 2


def test_must_read_env_float() -> None:
    os.environ["FLOAT"] = "1.23456"
    value = must_read_env_float("FLOAT")
    assert isinstance(value, float)
    assert value == 1.23456


def test_must_read_env_bool() -> None:
    os.environ["T_BOOL"] = "True"
    value = must_read_env_bool("T_BOOL")
    assert isinstance(value, bool)
    assert value

    os.environ["F_BOOL"] = "False"
    value = must_read_env_bool("F_BOOL")
    assert isinstance(value, bool)
    assert not value


def test_read_env_str_with_default() -> None:
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


def test_missing_env() -> None:
    str_value = read_env_str("MISSING")
    assert str_value is None

    int_value = read_env_int("MISSING")
    assert int_value is None

    float_value = read_env_float("MISSING")
    assert float_value is None

    bool_value = read_env_bool("MISSING")
    assert bool_value is None

    with pytest.raises(MissingEnvVariableException):
        must_read_env_str("MISSING")

    with pytest.raises(MissingEnvVariableException):
        must_read_env_int("MISSING")

    with pytest.raises(MissingEnvVariableException):
        must_read_env_float("MISSING")

    with pytest.raises(MissingEnvVariableException):
        must_read_env_bool("MISSING")


def test_invalid_env() -> None:
    os.environ["INVALID_INT"] = "NOT_AN_INT"
    with pytest.raises(EnvVariableValueException):
        read_env_int("INVALID_INT")

    os.environ["INVALID_FLOAT"] = "2Gb"
    with pytest.raises(EnvVariableValueException):
        read_env_float("INVALID_FLOAT")

    os.environ["INVALID_BOOL"] = "Tue"
    with pytest.raises(EnvVariableValueException):
        must_read_env_bool("INVALID_BOOL")
