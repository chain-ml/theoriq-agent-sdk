from __future__ import annotations

from typing import Any, Dict, Optional

from .schemas import BaseData, ItemBlock


class TextItem(BaseData):
    """ """

    def __init__(self, text: str):
        self.text = text

    def to_dict(self) -> Dict[str, Any]:
        return {"text": self.text}


class TextItemBlock(ItemBlock[TextItem]):
    """ """

    def __init__(self, text: str, sub_type: Optional[str] = None):
        sub_type = f":{sub_type}" if sub_type is not None else ""
        super().__init__(bloc_type=f"text{sub_type}", data=TextItem(text=text))

    @classmethod
    def from_dict(cls, data: Any):
        return cls(text=data["text"])
