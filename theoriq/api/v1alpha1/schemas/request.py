from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from theoriq.dialog import Dialog, DialogItem, DialogItemPredicate
from theoriq.types import SourceType


class ExecuteRequestBody(BaseModel):
    """
    A class representing the body of an execute request. Inherits from BaseModel.
    """

    dialog: Dialog

    @property
    def last_item(self) -> Optional[DialogItem]:
        """
        Returns the last dialog item contained in the request based on the timestamp.

        Returns:
            Optional[DialogItem]: The dialog item with the most recent timestamp, or None if there are no items.
        """
        if len(self.dialog.items) == 0:
            return None
        # Finds and returns the dialog item with the latest timestamp.
        return max(self.dialog.items, key=lambda obj: obj.timestamp)

    def last_item_from(self, source_type: SourceType) -> Optional[DialogItem]:
        """
        Returns the last dialog item from a specific source type based on the timestamp.

        Args:
            source_type (SourceType): The source type to filter the dialog items.

        Returns:
            Optional[DialogItem]: The dialog item with the most recent timestamp from the specified source type,
                                  or None if no items match the source type.
        """
        # Filters items by source type and finds the one with the latest timestamp.
        return self.last_item_predicate(lambda item: item.source_type == source_type)

    def last_item_predicate(self, predicate: DialogItemPredicate) -> Optional[DialogItem]:
        """
        Returns the last dialog item that matches the given predicate based on the timestamp.

        Args:
            predicate (DialogItemPredicate): A function that takes a DialogItem and returns a boolean.

            Returns:
                Optional[DialogItem]: The dialog item that matches the predicate and has the latest timestamp,
                                       or None if no items match the predicate.
        """

        # Filters items matching the given predicate and finds the one with the latest timestamp.
        items = (item for item in self.dialog.items if predicate(item))
        return max(items, key=lambda obj: obj.timestamp) if items else None
