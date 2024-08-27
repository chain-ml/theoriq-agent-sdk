from __future__ import annotations

from typing import Any, Dict, Optional

from .schemas import BaseData, ItemBlock


class CodeItem(BaseData):
    """
    A class representing a code item. Inherits from BaseData.
    """

    def __init__(self, code: str) -> None:
        """
        Initializes a CodeItem instance.

        Args:
            code (str): The code string to be stored in this CodeItem.
        """
        self.code = code

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the CodeItem instance into a dictionary.

        Returns:
            Dict[str, Any]: A dictionary with the code stored under the 'code' key.
        """
        return {"code": self.code}


class CodeItemBlock(ItemBlock[CodeItem]):
    """
    A class representing a block of code items. Inherits from ItemBlock with CodeItem as the generic type.
    """

    def __init__(self, *, code: str, language: Optional[str] = None) -> None:
        """
        Initializes a CodeItemBlock instance.

        Args:
            code (str): The code string to be stored in the block.
            language (Optional[str]): The programming language of the code. Defaults to None.
        """
        # Determines the subtype based on the language provided, if any.
        sub_type = f":{language}" if language is not None else ""
        # Calls the parent class constructor with the composed block type and a CodeItem instance.
        super().__init__(bloc_type=f"{CodeItemBlock.block_type()}{sub_type}", data=CodeItem(code=code))

    @classmethod
    def from_dict(cls, data: Any, block_type: str) -> CodeItemBlock:
        """
        Creates an instance of CodeItemBlock from a dictionary.

        Args:
            data (Any): The data dictionary containing the code string.
            block_type (str): The type of the block.

        Returns:
            CodeItemBlock: A new instance of CodeItemBlock initialized with the provided data.
        """
        # Ensures the block type is valid before proceeding.
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        # Returns a new instance of CodeItemBlock using the code from the data dictionary.
        return cls(code=data["code"], language=cls.sub_type(block_type))

    @classmethod
    def block_type(cls) -> str:
        """
        Returns the block type for CodeItemBlock.

        Returns:
            str: The string 'code', representing the block type.
        """
        return "code"

    @classmethod
    def is_valid(cls, block_type: str) -> bool:
        """
        Checks if the provided block type is valid for a CodeItemBlock.

        Args:
            block_type (str): The block type to validate.

        Returns:
            bool: True if the block type is valid, False otherwise.
        """
        # Validates that the block type starts with the expected 'code' block type.
        return block_type.startswith(CodeItemBlock.block_type())
