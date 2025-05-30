from __future__ import annotations

from typing import Any, Dict, Optional

from .item_block import BaseData, ItemBlock


class ErrorItem(BaseData):
    """
    A class representing an error item. Inherits from BaseData.
    """

    def __init__(self, err: str, message: Optional[str]) -> None:
        """
        Initializes an ErrorItem instance.

        Args:
            err (str): The error code or identifier.
            message (Optional[str]): An optional message providing additional details about the error.
        """
        self.err = err
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the ErrorItem instance into a dictionary.

        Returns:
            Dict[str, Any]: A dictionary with the error code and optionally the message.
        """
        result = {"error": self.err}
        if self.message:
            result["message"] = self.message
        return result

    def to_str(self) -> str:
        result = [f"- Error: {self.err}"]
        if self.message is not None:
            result.append(f"- Message: {self.message}")
        return "\n".join(result)

    @classmethod
    def from_dict(cls, values: Dict[str, Any]) -> ErrorItem:
        """
        Creates an instance of ErrorItem from a dictionary.

        Args:
            values (Dict[str, Any]): The dictionary containing the error code and optionally the message.

        Returns:
            ErrorItem: A new instance of ErrorItem initialized with the provided values.
        """
        return cls(err=values["error"], message=values.get("message"))

    def __str__(self) -> str:
        """
        Returns a string representation of the ErrorItem instance.

        Returns:
            str: A string representing the ErrorItem.
        """
        return f"ErrorItem(err={self.err}, message={self.message})"


class ErrorItemBlock(ItemBlock[ErrorItem]):
    """
    A class representing a block of error items. Inherits from ItemBlock with ErrorItem as the generic type.
    """

    def __init__(
        self,
        err: ErrorItem,
        key: Optional[str] = None,
        reference: Optional[str] = None,
    ) -> None:
        """
        Initializes an ErrorItemBlock instance.

        Args:
            err (ErrorItem): An instance of ErrorItem to be stored in the block.
        """
        super().__init__(block_type=ErrorItemBlock.block_type(), data=err, key=key, reference=reference)

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], block_type: str, block_key: Optional[str] = None, block_ref: Optional[str] = None
    ) -> ErrorItemBlock:
        """
        Creates an instance of ErrorItemBlock from a dictionary.

        Args:
            data (Dict[str, Any]): The dictionary containing the error item data.
            block_type (str): The type of the block.
            block_key (Optional[str]): An optional key to uniquely identify the block.
            block_ref (Optional[str]): An optional reference to external data.

        Returns:
            ErrorItemBlock: A new instance of ErrorItemBlock initialized with the provided data.
        """
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        values = data.get("error")
        if values is None:
            raise ValueError("Missing 'error' key")
        return cls(err=ErrorItem.from_dict(data), key=block_key, reference=block_ref)

    @staticmethod
    def block_type() -> str:
        """
        Returns the block type for ErrorItemBlock.

        Returns:
            str: The string 'error', representing the block type.
        """
        return "error"

    @staticmethod
    def is_valid(block_type: str) -> bool:
        """
        Checks if the provided block type is valid for an ErrorItemBlock.

        Args:
            block_type (str): The block type to validate.

        Returns:
            bool: True if the block type is valid, False otherwise.
        """
        return block_type.startswith(ErrorItemBlock.block_type())

    @classmethod
    def new(cls, err: str, message: Optional[str]) -> ErrorItemBlock:
        """
        Creates a new instance of ErrorItemBlock with a given error code and optional message.

        Args:
            err (str): The error code or identifier.
            message (Optional[str]): An optional message providing additional details about the error.

        Returns:
            ErrorItemBlock: A new instance of ErrorItemBlock initialized with the provided error data.
        """
        return cls(err=ErrorItem(err=err, message=message))
