from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

from .schemas import BaseData, ItemBlock


class RouteItem(BaseData):
    """
    A class representing a single route item. Inherits from BaseData.
    """

    def __init__(self, name: str, score: float, reason: Optional[str] = None) -> None:
        """
        Initializes a RouteItem instance.

        Args:
            name (str): The name of the route.
            score (float): The score associated with the route.
            reason (Optional[str]): An optional reason for the score. Defaults to None.
        """
        self.name = name
        self.score = score
        self.reason = reason

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the RouteItem instance into a dictionary.

        Returns:
            Dict[str, Any]: A dictionary with the route's name, score, and optionally the reason.
        """
        result = {"name": self.name, "score": self.score}
        if self.reason is not None:
            result["reason"] = self.reason
        return result

    @classmethod
    def from_dict(cls, values: Dict[str, Any]) -> RouteItem:
        """
        Creates an instance of RouteItem from a dictionary.

        Args:
            values (Dict[str, Any]): The dictionary containing the route's name, score, and optionally the reason.

        Returns:
            RouteItem: A new instance of RouteItem initialized with the provided values.
        """
        return cls(name=values["name"], score=values["score"], reason=values.get("reason"))

    def __str__(self):
        """
        Returns a string representation of the RouteItem instance.

        Returns:
            str: A string representing the RouteItem.
        """
        return f"RouteItem(name={self.name}, score={self.score})"


class RouterItemBlock(ItemBlock[Sequence[RouteItem]]):
    """
    A class representing a block of route items. Inherits from ItemBlock with a sequence of RouteItem as the generic type.
    """

    def __init__(self, routes: Sequence[RouteItem], **kwargs) -> None:
        """
        Initializes a RouterItemBlock instance.

        Args:
            routes (Sequence[RouteItem]): A sequence of RouteItem instances to be stored in the block.
        """
        super().__init__(bloc_type=RouterItemBlock.block_type(), data=routes, **kwargs)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], block_type: str) -> RouterItemBlock:
        """
        Creates an instance of RouterItemBlock from a dictionary.

        Args:
            data (Dict[str, Any]): The dictionary containing the route items.
            block_type (str): The type of the block.

        Returns:
            RouterItemBlock: A new instance of RouterItemBlock initialized with the provided data.
        """
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        items = data.get("items", [])
        # Converts each dictionary in 'items' into a RouteItem instance.
        return cls(routes=[RouteItem.from_dict(route) for route in items])

    def best(self) -> RouteItem:
        """
        Finds and returns the RouteItem with the highest score.

        Returns:
            RouteItem: The RouteItem instance with the highest score.
        """
        return max(self.data, key=lambda obj: obj.score)

    @classmethod
    def block_type(cls) -> str:
        """
        Returns the block type for RouterItemBlock.

        Returns:
            str: The string 'router', representing the block type.
        """
        return "router"

    @classmethod
    def is_valid(cls, block_type: str) -> bool:
        """
        Checks if the provided block type is valid for a RouterItemBlock.

        Args:
            block_type (str): The block type to validate.

        Returns:
            bool: True if the block type is valid, False otherwise.
        """
        return block_type == RouterItemBlock.block_type()
