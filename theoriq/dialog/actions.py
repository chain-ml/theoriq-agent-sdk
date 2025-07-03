from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

from .item_block import BaseData, ItemBlock


class ActionItem(BaseData):
    """A single user-selectable action such as a button.

    Attributes
    ----------
    id: str
        A unique identifier within the surrounding ActionsItemBlock. Will be echoed back when the
        user selects the action.
    label: str
        Human-readable label for UI display (e.g. button text).
    description: Optional[str]
        Longer explanation or tooltip. Optional so CLI renderings can ignore it.
    payload: Optional[Dict[str, Any]]
        Arbitrary data for the consumer to echo back (e.g. a router target, parameters, etc.).
    """

    def __init__(
        self,
        *,
        id: str,
        label: str,
        description: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.id = id
        self.label = label
        self.description = description
        self.payload = payload

    @classmethod
    def from_dict(cls, values: Dict[str, Any]) -> "ActionItem":
        return cls(
            id=values["id"],
            label=values["label"],
            description=values.get("description"),
            payload=values.get("payload"),
        )

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"id": self.id, "label": self.label}
        if self.description is not None:
            result["description"] = self.description
        if self.payload is not None:
            result["payload"] = self.payload
        return result

    def to_str(self) -> str:  # pragma: no cover – only used for debug / CLI
        """Human-readable representation used by Dialog.format_as_markdown()."""
        result = f"- {self.label} (id: {self.id})"
        if self.description:
            result += f" – {self.description}"
        return result

    def __str__(self) -> str:
        return f"ActionItem(id={self.id}, label={self.label})"


class ActionsItemBlock(ItemBlock[Sequence[ActionItem]]):
    """A block containing a list of available actions."""

    def __init__(
        self,
        actions: Sequence[ActionItem],
        *,
        key: Optional[str] = None,
        reference: Optional[str] = None,
    ) -> None:
        super().__init__(block_type=self.block_type(), data=actions, key=key, reference=reference)

    # ---------------------------------------------------------------------
    # ItemBlock interface helpers
    # ---------------------------------------------------------------------

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        block_type: str,
        block_key: Optional[str] = None,
        block_ref: Optional[str] = None,
    ) -> "ActionsItemBlock":
        cls.raise_if_not_valid(block_type=block_type, expected=cls.block_type())
        items = data.get("items", [])
        return cls(actions=[ActionItem.from_dict(it) for it in items], key=block_key, reference=block_ref)

    @staticmethod
    def block_type() -> str:
        return "actions"

    @staticmethod
    def is_valid(block_type: str) -> bool:
        return block_type == ActionsItemBlock.block_type()

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    def find(self, action_id: str) -> Optional[ActionItem]:
        """Return an action by its *id* or None if not found."""
        return next((a for a in self.data if a.id == action_id), None)
