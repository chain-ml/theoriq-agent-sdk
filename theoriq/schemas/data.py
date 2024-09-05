from __future__ import annotations

from typing import Any, Dict, Optional

from .schemas import BaseData, ItemBlock


class DataItem(BaseData):
    """
    A class representing a data item. Inherits from BaseData.
    """

    def __init__(self, data: str) -> None:
        """
        Initializes a DataItem instance.

        Args:
            data (str): The data string to be stored in this DataItem.
        """
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the DataItem instance into a dictionary.

        Returns:
            Dict[str, Any]: A dictionary with the data stored under the 'data' key.
        """
        return {"data": self.data}

    def __str__(self):
        """
        Returns a string representation of the DataItem instance.

        Returns:
            str: A string representing the DataItem.
        """
        data = self.data if len(self.data) < 50 else f"{self.data[:50]}..."
        return f"DataItem(data={data})"


class DataItemBlock(ItemBlock[DataItem]):
    """
    A class representing a block of data items. Inherits from ItemBlock with DataItem as the generic type.
    """

    def __init__(self, *, data: str, data_type: Optional[str] = None, **kwargs) -> None:
        """
        Initializes a DataItemBlock instance.

        Args:
            data (str): The data string to be stored in the block.
            data_type (Optional[str]): The type of the data. Defaults to None.
        """
        # Determines the subtype based on the data_type provided, if any.
        sub_type = f":{data_type}" if data_type is not None else ""
        # Calls the parent class constructor with the composed block type and a DataItem instance.
        super().__init__(bloc_type=f"{DataItemBlock.block_type()}{sub_type}", data=DataItem(data=data), **kwargs)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], block_type: str) -> DataItemBlock:
        """
        Creates an instance of DataItemBlock from a dictionary.

        Args:
            data (Dict[str, Any]): The data dictionary containing the data string.
            block_type (str): The type of the block.

        Returns:
            DataItemBlock: A new instance of DataItemBlock initialized with the provided data.
        """
        # Ensures the block type is valid before proceeding.
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        # Returns a new instance of DataItemBlock using the data from the dictionary.
        return cls(data=data["data"], data_type=cls.sub_type(block_type))

    @classmethod
    def block_type(cls) -> str:
        """
        Returns the block type for DataItemBlock.

        Returns:
            str: The string 'data', representing the block type.
        """
        return "data"

    @classmethod
    def is_valid(cls, block_type: str) -> bool:
        """
        Checks if the provided block type is valid for a DataItemBlock.

        Args:
            block_type (str): The block type to validate.

        Returns:
            bool: True if the block type is valid, False otherwise.
        """
        # Validates that the block type starts with the expected 'data' block type.
        return block_type.startswith(DataItemBlock.block_type())
