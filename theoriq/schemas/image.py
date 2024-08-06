from __future__ import annotations

import base64
import mimetypes
from typing import Any, Dict, Optional

from .schemas import BaseData, ItemBlock


class ImageItem(BaseData):
    """ """

    def __init__(self, base64: str) -> None:
        self.base64 = base64

    def to_dict(self) -> Dict[str, Any]:
        return {"base64": self.base64}


class ImageItemBlock(ItemBlock[ImageItem]):
    """ """

    def __init__(self, base64: str, sub_type: Optional[str] = None) -> None:
        sub_type = f":{sub_type}" if sub_type is not None else ""
        super().__init__(bloc_type=f"{ImageItemBlock.block_type()}{sub_type}", data=ImageItem(base64=base64))

    @classmethod
    def from_dict(cls, data: Any, block_type: str) -> ImageItemBlock:
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        return cls(base64=data["base64"], sub_type=cls.sub_type(block_type))

    @classmethod
    def from_file(cls, path: str) -> ImageItemBlock:
        mime_type, _ = mimetypes.guess_type(path)
        sub_type = mime_type.split("/")[-1] if mime_type else ""

        with open(path, "rb") as f:
            return cls(base64=base64.b64encode(f.read()).decode("utf-8"), sub_type=sub_type)

    @staticmethod
    def block_type() -> str:
        return "image"

    @staticmethod
    def is_valid(block_type: str) -> bool:
        return block_type.startswith(ImageItemBlock.block_type())
