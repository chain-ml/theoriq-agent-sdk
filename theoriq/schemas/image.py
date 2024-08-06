from __future__ import annotations

import base64
from typing import Any, Dict, Optional
import mimetypes

from .schemas import BaseData, ItemBlock


class ImageItem(BaseData):
    """ """

    def __init__(self, base64: str):
        self.base64 = base64

    def to_dict(self) -> Dict[str, Any]:
        return {"base64": self.base64}


class ImageItemBlock(ItemBlock[ImageItem]):
    """ """

    def __init__(self, base64: str, sub_type: Optional[str] = None):
        sub_type = f":{sub_type}" if sub_type is not None else ""
        super().__init__(bloc_type=f"text{sub_type}", data=ImageItem(base64=base64))

    @classmethod
    def from_dict(cls, data: Any):
        return cls(base64=data["base64"])

    @classmethod
    def from_file(cls, path: str) -> ImageItemBlock:
        mime_type, _ = mimetypes.guess_type(path)
        sub_type = mime_type.split("/")[-1] or ""

        with open(path, "rb") as f:
            return cls(base64=base64.b64encode(f.read()).decode("utf-8"), sub_type=sub_type)
