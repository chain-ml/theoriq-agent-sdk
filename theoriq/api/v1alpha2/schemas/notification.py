from __future__ import annotations

from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

from theoriq.dialog.block import BaseTheoriqModel

T = TypeVar("T", bound=BaseModel)


class NotificationContext(BaseTheoriqModel):
    """
    Represents a notification message with optional configuration.
    """

    notification: str
    configuration: Optional[Dict[str, Any]] = None

    def try_parse_configuration(self, configuration_cls: Type[T]) -> Optional[T]:
        if self.configuration is None:
            return None

        try:
            return configuration_cls.model_validate(self.configuration)
        except ValidationError:
            return None
