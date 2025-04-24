import os
from typing import Any, Optional, Final

DATA_DIR: Final[str] = os.path.join(os.path.dirname(__file__), "data")


class OsEnviron:
    def __init__(self, name: str, value: Optional[Any] = None):
        self.name = name
        self.value = str(value) if value is not None else None
        self.previous_value = None

    def __enter__(self):
        self.previous_value = os.environ.get(self.name, None)
        self._set(self.value)

    def __exit__(self, exception_type, exception_value, traceback):
        self._set(self.previous_value)

    def _set(self, value: Optional[str]):
        os.environ.pop(self.name, None)
        if value is not None:
            os.environ[self.name] = value

    def __str__(self) -> str:
        return f"Env var:`{self.name}` value:{self.value} (previous value: {self.previous_value})"
