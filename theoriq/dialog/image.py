from __future__ import annotations

import base64
import mimetypes
from typing import Any, Dict, Optional

from .item_block import BaseData, ItemBlock


class ImageItem(BaseData):
    """
    A class representing an image item. Inherits from BaseData.
    """

    def __init__(self, image: str) -> None:
        """
        Initializes an ImageItem instance.

        Args:
            image (str): The base64 encoded string representing the image.
        """
        self.base64 = image

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the ImageItem instance into a dictionary.

        Returns:
            Dict[str, Any]: A dictionary with the base64 encoded image stored under the 'base64' key.
        """
        return {"base64": self.base64}

    def to_str(self) -> str:
        return self.base64

    def __str__(self):
        """
        Returns a string representation of the ImageItem instance.

        Returns:
            str: A string representing the ImageItem.
        """
        image_base64 = self.base64 if len(self.base64) < 50 else f"{self.base64[:50]}..."
        return f"ImageItem(base64={image_base64})"


class ImageItemBlock(ItemBlock[ImageItem]):
    """
    A class representing a block of image items. Inherits from ItemBlock with ImageItem as the generic type.
    """

    def __init__(
        self,
        image_base64: str,
        sub_type: Optional[str] = None,
        key: Optional[str] = None,
        reference: Optional[str] = None,
    ) -> None:
        """
        Initializes an ImageItemBlock instance.

        Args:
            image_base64 (str): The base64 encoded string representing the image.
            sub_type (Optional[str]): The subtype of the image (e.g., 'png', 'jpeg'). Defaults to None.
        """
        # Determines the subtype based on the provided sub_type, if any.
        sub_type = f":{sub_type}" if sub_type is not None else ""
        block_type = f"{ImageItemBlock.block_type()}{sub_type}"
        super().__init__(block_type=block_type, data=ImageItem(image=image_base64), key=key, reference=reference)

    @classmethod
    def from_dict(
        cls, data: Any, block_type: str, block_key: Optional[str] = None, block_ref: Optional[str] = None
    ) -> ImageItemBlock:
        """
        Creates an instance of ImageItemBlock from a dictionary.

        Args:
            data (Any): The data dictionary containing the base64 encoded image string.
            block_type (str): The type of the block.

        Returns:
            ImageItemBlock: A new instance of ImageItemBlock initialized with the provided data.
        """
        # Ensures the block type is valid before proceeding.
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        # Returns a new instance of ImageItemBlock using the base64 image string from the data dictionary.
        return cls(image_base64=data["base64"], sub_type=cls.sub_type(block_type), key=block_key, reference=block_ref)

    @classmethod
    def from_file(cls, path: str) -> ImageItemBlock:
        """
        Creates an instance of ImageItemBlock from an image file.

        Args:
            path (str): The path to the image file.

        Returns:
            ImageItemBlock: A new instance of ImageItemBlock initialized with the base64 encoded image string from the file.
        """
        # Determines the MIME type of the file to extract the subtype (e.g., 'png', 'jpeg').
        mime_type, _ = mimetypes.guess_type(path)
        sub_type = mime_type.split("/")[-1] if mime_type else ""

        # Opens the file in binary mode, reads its contents, and encodes it to a base64 string.
        with open(path, "rb") as f:
            return cls(image_base64=base64.b64encode(f.read()).decode("utf-8"), sub_type=sub_type)

    @staticmethod
    def block_type() -> str:
        """
        Returns the block type for ImageItemBlock.

        Returns:
            str: The string 'image', representing the block type.
        """
        return "image"

    @staticmethod
    def is_valid(block_type: str) -> bool:
        """
        Checks if the provided block type is valid for an ImageItemBlock.

        Args:
            block_type (str): The block type to validate.

        Returns:
            bool: True if the block type is valid, False otherwise.
        """
        # Validates that the block type starts with the expected 'image' block type.
        return block_type.startswith(ImageItemBlock.block_type())
