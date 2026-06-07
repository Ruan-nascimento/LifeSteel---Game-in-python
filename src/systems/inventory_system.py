from __future__ import annotations

from dataclasses import dataclass

from src.data.items_data import ITEMS
from src.items.item import Item, make_item


@dataclass
class InventorySlot:
    item_id: str
    quantity: int = 1
    durability: int | None = None
    contents: list["InventorySlot | None"] | None = None

    @property
    def item(self) -> Item:
        return make_item(self.item_id)

    @property
    def is_empty(self) -> bool:
        return self.quantity <= 0

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "quantity": self.quantity,
            "durability": self.durability,
            "contents": [
                slot.to_dict() if slot else None
                for slot in self.contents
            ] if self.contents is not None else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InventorySlot":
        return cls(
            item_id=data["item_id"],
            quantity=int(data.get("quantity", 1)),
            durability=data.get("durability"),
            contents=[
                cls.from_dict(slot) if slot else None
                for slot in data.get("contents") or []
            ] if data.get("contents") is not None else None,
        )

    def clone(self) -> "InventorySlot":
        return InventorySlot.from_dict(self.to_dict())

    @property
    def container_capacity(self) -> int:
        return int(ITEMS[self.item_id].get("container_slots", 0))

    def is_container(self) -> bool:
        return self.container_capacity > 0

    def ensure_contents(self) -> list["InventorySlot | None"]:
        if not self.is_container():
            return []
        if self.contents is None:
            self.contents = [None for _ in range(self.container_capacity)]
        elif len(self.contents) < self.container_capacity:
            self.contents.extend([None for _ in range(self.container_capacity - len(self.contents))])
        return self.contents


class Inventory:
    def __init__(self, capacity: int = 20) -> None:
        self.capacity = capacity
        self.slots: list[InventorySlot | None] = [None for _ in range(capacity)]
        self.selected_slot = 0
        self.selected_category = "Todos"

    def __iter__(self):
        return iter(self.slots)

    def add_item(self, item_id: str, quantity: int = 1, durability: int | None = None) -> int:
        if item_id not in ITEMS or quantity <= 0:
            return quantity

        data = ITEMS[item_id]
        max_stack = int(data.get("max_stack", 1 if not data.get("stackable", True) else 99))
        stackable = bool(data.get("stackable", True))

        if stackable:
            for slot in self.slots:
                if slot and slot.item_id == item_id and slot.quantity < max_stack:
                    moved = min(quantity, max_stack - slot.quantity)
                    slot.quantity += moved
                    quantity -= moved
                    if quantity <= 0:
                        return 0

        for index, slot in enumerate(self.slots):
            if slot is None:
                moved = min(quantity, max_stack)
                slot = InventorySlot(item_id, moved, durability)
                if ITEMS[item_id].get("container_slots"):
                    slot.ensure_contents()
                self.slots[index] = slot
                quantity -= moved
                if quantity <= 0:
                    return 0

        return quantity

    def free_space_for(self, item_id: str) -> int:
        if item_id not in ITEMS:
            return 0
        data = ITEMS[item_id]
        stackable = bool(data.get("stackable", True))
        max_stack = int(data.get("max_stack", 1 if not stackable else 99))
        space = 0
        if stackable:
            for slot in self.slots:
                if slot and slot.item_id == item_id and slot.contents is None:
                    space += max(0, max_stack - slot.quantity)
        for slot in self.slots:
            if slot is None:
                space += max_stack
        return space

    def can_accept_item(self, item_id: str, quantity: int = 1) -> bool:
        return self.free_space_for(item_id) >= quantity

    def add_slot(self, incoming: InventorySlot) -> bool:
        slot = incoming.clone()
        data = ITEMS.get(slot.item_id, {})
        stackable = bool(data.get("stackable", True)) and slot.contents is None
        max_stack = int(data.get("max_stack", 1 if not stackable else 99))
        if stackable:
            remaining = slot.quantity
            for existing in self.slots:
                if existing and existing.item_id == slot.item_id and existing.quantity < max_stack and existing.contents is None:
                    moved = min(remaining, max_stack - existing.quantity)
                    existing.quantity += moved
                    remaining -= moved
                    if remaining <= 0:
                        return True
            slot.quantity = remaining
        for index, existing in enumerate(self.slots):
            if existing is None:
                self.slots[index] = slot
                return True
        return False

    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        if self.count(item_id) < quantity:
            return False
        remaining = quantity
        for index, slot in enumerate(self.slots):
            if slot and slot.item_id == item_id:
                take = min(slot.quantity, remaining)
                slot.quantity -= take
                remaining -= take
                if slot.quantity <= 0:
                    self.slots[index] = None
                if remaining <= 0:
                    return True
        return True

    def remove_from_slot(self, index: int, quantity: int = 1) -> InventorySlot | None:
        if index < 0 or index >= len(self.slots):
            return None
        slot = self.slots[index]
        if not slot:
            return None
        removed = InventorySlot(slot.item_id, min(quantity, slot.quantity), slot.durability, [
            content.clone() if content else None
            for content in slot.contents
        ] if slot.contents is not None else None)
        slot.quantity -= removed.quantity
        if slot.quantity <= 0:
            self.slots[index] = None
        return removed

    def move_slot(self, source: int, target: int) -> None:
        if source == target:
            return
        if not (0 <= source < self.capacity and 0 <= target < self.capacity):
            return
        self.slots[source], self.slots[target] = self.slots[target], self.slots[source]

    def swap_with_slots(self, source: int, target_slots: list[InventorySlot | None], target: int) -> None:
        if not (0 <= source < self.capacity and 0 <= target < len(target_slots)):
            return
        self.slots[source], target_slots[target] = target_slots[target], self.slots[source]

    def count(self, item_id: str) -> int:
        return sum(slot.quantity for slot in self.slots if slot and slot.item_id == item_id)

    def first_slot_with(self, item_id: str) -> int | None:
        for index, slot in enumerate(self.slots):
            if slot and slot.item_id == item_id:
                return index
        return None

    def selected(self) -> InventorySlot | None:
        if self.selected_slot is not None and 0 <= self.selected_slot < self.capacity:
            return self.slots[self.selected_slot]
        return None

    def selected_item(self) -> Item | None:
        slot = self.selected()
        return slot.item if slot else None

    def can_pay(self, costs: dict[str, int]) -> bool:
        return all(self.count(item_id) >= amount for item_id, amount in costs.items())

    def pay(self, costs: dict[str, int]) -> bool:
        if not self.can_pay(costs):
            return False
        for item_id, amount in costs.items():
            self.remove_item(item_id, amount)
        return True

    def filtered_slots(self, category: str) -> list[tuple[int, InventorySlot]]:
        result = []
        for index, slot in enumerate(self.slots):
            if not slot:
                continue
            if category == "Todos" or ITEMS[slot.item_id].get("category") == category:
                result.append((index, slot))
        return result

    def to_list(self) -> list[dict | None]:
        return [slot.to_dict() if slot else None for slot in self.slots]

    @classmethod
    def from_list(cls, data: list[dict | None], capacity: int = 20) -> "Inventory":
        inventory = cls(max(capacity, len(data)))
        inventory.slots = [
            InventorySlot.from_dict(slot) if slot else None
            for slot in data
        ]
        inventory.capacity = len(inventory.slots)
        return inventory
