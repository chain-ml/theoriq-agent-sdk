from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

from theoriq.dialog.block import BaseTheoriqModel

T = TypeVar("T", bound=BaseModel)


class VirtualAgentNotification(BaseTheoriqModel):
    """Represents a notification message with virtual agent's configuration."""

    notification: str
    configuration: Dict[str, Any]

    def try_parse_configuration(self, configuration_cls: Type[T]) -> Optional[T]:
        try:
            return configuration_cls.model_validate(self.configuration)
        except ValidationError:
            return None
