from __future__ import annotations

from typing import Optional

from theoriq.dialog import BaseData, Dialog, DialogItem, DialogItemPredicate
from theoriq.types import SourceType


class ConfigurationRef(BaseData):
    """
    Represents the expected payload for a configuration request.
    """

    hash: str
    id: str


class Configuration(BaseData):
    """
    Represents the expected payload for a configuration request.
    """

    fromRef: ConfigurationRef


class ExecuteRequestBody(BaseData):
    """
    A class representing the body of an execute request. Inherits from BaseModel.
    """

    configuration: Optional[Configuration] = None
    dialog: Dialog

    @property
    def last_item(self) -> Optional[DialogItem]:
        return self.dialog.last_item

    @property
    def last_text(self) -> str:
        return self.dialog.last_text

    def last_item_from(self, source_type: SourceType) -> Optional[DialogItem]:
        return self.dialog.last_item_from(source_type)

    def last_item_predicate(self, predicate: DialogItemPredicate) -> Optional[DialogItem]:
        return self.dialog.last_item_predicate(predicate)
