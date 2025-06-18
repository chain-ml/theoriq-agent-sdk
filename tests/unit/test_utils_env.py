import os

import pytest

from theoriq.utils import (
    EnvVariableValueException,
    MissingEnvVariableException,
    read_env_bool,
    read_env_float,
    read_env_int,
    read_env_str,
)


def test_read_env_str() -> None:
    os.environ["STR"] = "VALUE"
    value = read_env_str("STR", required=True)
    assert isinstance(value, str)
    assert value == "VALUE"


def test_read_env_int() -> None:
    os.environ["INT"] = "2"
    value = read_env_int("INT", required=True)
    assert isinstance(value, int)
    assert value == 2


def test_read_env_float() -> None:
    os.environ["FLOAT"] = "1.23456"
    value = read_env_float("FLOAT", required=True)
    assert isinstance(value, float)
    assert value == 1.23456


def test_read_env_bool() -> None:
    os.environ["T_BOOL"] = "True"
    value = read_env_bool("T_BOOL", required=True)
    assert isinstance(value, bool)
    assert value

    os.environ["F_BOOL"] = "False"
    value = read_env_bool("F_BOOL", required=True)
    assert isinstance(value, bool)
    assert not value


def test_missing_env_with_default() -> None:
    value = read_env_int("MISSING_INT", default=2)
    assert isinstance(value, int)
    assert value == 2


def test_missing_env() -> None:
    value = read_env_str("MISSING")
    assert value is None

    with pytest.raises(MissingEnvVariableException):
        read_env_str("MISSING", required=True)


def test_invalid_env() -> None:
    os.environ["INVALID_FLOAT"] = "2Gb"
    with pytest.raises(EnvVariableValueException):
        read_env_float("INVALID_FLOAT")

    os.environ["INVALID_BOOL"] = "Tue"
    with pytest.raises(EnvVariableValueException):
        read_env_bool("INVALID_BOOL")
