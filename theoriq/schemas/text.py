from __future__ import annotations

from typing import Any, Dict, Optional

from .schemas import BaseData, ItemBlock


class TextItem(BaseData):
    """
    A class representing a text item. Inherits from BaseData.
    """

    def __init__(self, text: str) -> None:
        """
        Initializes a TextItem instance.

        Args:
            text (str): The text content to be stored in this TextItem.
        """
        self.text = text

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the TextItem instance into a dictionary.

        Returns:
            Dict[str, Any]: A dictionary with the text stored under the 'text' key.
        """
        return {"text": self.text}


class TextItemBlock(ItemBlock[TextItem]):
    """
    A class representing a block of text items. Inherits from ItemBlock with TextItem as the generic type.
    """

    def __init__(self, text: str, sub_type: Optional[str] = None) -> None:
        """
        Initializes a TextItemBlock instance.

        Args:
            text (str): The text content to be stored in the block.
            sub_type (Optional[str]): An optional subtype to categorize the text block. Defaults to None.
        """
        # Determines the subtype based on the provided sub_type, if any.
        sub_type = f":{sub_type}" if sub_type is not None else ""
        # Calls the parent class constructor with the composed block type and a TextItem instance.
        super().__init__(bloc_type=f"{TextItemBlock.block_type()}{sub_type}", data=TextItem(text=text))

    @classmethod
    def from_dict(cls, data: Dict[str, Any], block_type: str) -> TextItemBlock:
        """
        Creates an instance of TextItemBlock from a dictionary.

        Args:
            data (Dict[str, Any]): The dictionary containing the text content.
            block_type (str): The type of the block.

        Returns:
            TextItemBlock: A new instance of TextItemBlock initialized with the provided data.
        """
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        return cls(text=data["text"], sub_type=cls.sub_type(block_type))

    @classmethod
    def block_type(cls) -> str:
        """
        Returns the block type for TextItemBlock.

        Returns:
            str: The string 'text', representing the block type.
        """
        return "text"

    @classmethod
    def is_valid(cls, block_type: str) -> bool:
        """
        Checks if the provided block type is valid for a TextItemBlock.

        Args:
            block_type (str): The block type to validate.

        Returns:
            bool: True if the block type is valid, False otherwise.
        """
        return block_type.startswith(TextItemBlock.block_type())
