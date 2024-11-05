from __future__ import annotations

from typing import Optional, Dict, Any

from theoriq.dialog import ItemBlock


class EventRequest:
    def __init__(self, *, message: str, request_id: str, obj: Optional[ItemBlock] = None) -> None:
        self.message = message
        self.request_id = request_id
        self.obj = obj

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "message": self.message,
        }
        if self.obj is not None:
            result["object"] = self.obj.to_dict()
        return result
