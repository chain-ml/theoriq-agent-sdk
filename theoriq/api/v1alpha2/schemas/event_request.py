from __future__ import annotations

from typing import Any, Dict, Optional

from theoriq.dialog import BlockBase


class EventRequestBody:
    def __init__(self, *, message: str, request_id: str, obj: Optional[BlockBase] = None) -> None:
        self.message = message
        self.request_id = request_id
        self.obj = obj

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "message": self.message,
        }
        if self.obj is not None:
            result["object"] = self.obj.model_dump()
        return result
