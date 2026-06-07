from __future__ import annotations

from src.data.food_data import CONSUMABLE_TYPES
from src.data.items_data import ITEMS


ATTRIBUTE_LABELS = {
    "health": "Vida",
    "hunger": "Fome",
    "thirst": "Sede",
    "energy": "Energia",
    "mana": "Mana",
}

ATTRIBUTE_MAP = {
    "health": ("health", "max_health"),
    "hunger": ("hunger", "max_hunger"),
    "thirst": ("thirst", "max_thirst"),
    "energy": ("energy", "max_energy"),
    "mana": ("mana", "max_mana"),
}


class ConsumableSystem:
    def __init__(self, item_data: dict | None = None) -> None:
        self.item_data = item_data if item_data is not None else ITEMS
        self.message = "Consumiveis prontos."

    def consume(self, player, inventory, item_id: str, slot_index: int | None = None) -> dict:
        item = self.item_data.get(item_id)
        if not item:
            return self._failure("Item inexistente.")
        if item.get("type") not in CONSUMABLE_TYPES:
            return self._failure("Este item nao pode ser consumido.")

        index = self._find_slot(inventory, item_id, slot_index)
        if index is None:
            return self._failure("Item nao encontrado no inventario.")

        effects = self._effects_for(item)
        effects_applied = self._apply_effects(player, effects)
        removed = inventory.remove_from_slot(index, 1)
        if not removed:
            return self._failure("Nao foi possivel consumir este item.")

        effect_lines = self._effect_lines(effects_applied)
        item_name = item.get("name", item_id)
        self.message = f"Voce consumiu {item_name}."
        return {
            "success": True,
            "message": self.message,
            "item_id": item_id,
            "item_name": item_name,
            "effects_applied": effects_applied,
            "effect_lines": effect_lines,
        }

    def _find_slot(self, inventory, item_id: str, slot_index: int | None) -> int | None:
        if slot_index is not None:
            if 0 <= slot_index < inventory.capacity:
                slot = inventory.slots[slot_index]
                if slot and slot.item_id == item_id:
                    return slot_index
            return None
        return inventory.first_slot_with(item_id)

    def _effects_for(self, item: dict) -> dict[str, float]:
        effects = dict(item.get("effects") or {})
        if "health" not in effects and "heal" in item:
            effects["health"] = item["heal"]
        for key in ("hunger", "thirst", "energy", "mana", "mana_percent"):
            if key not in effects and key in item:
                effects[key] = item[key]
        return {key: float(value) for key, value in effects.items()}

    def _apply_effects(self, player, effects: dict[str, float]) -> dict[str, int]:
        applied: dict[str, int] = {key: 0 for key in ATTRIBUTE_LABELS}
        mana_percent = effects.get("mana_percent", 0)
        if mana_percent:
            effects = dict(effects)
            effects["mana"] = effects.get("mana", 0) + player.max_mana * (mana_percent / 100)
        for key in ATTRIBUTE_LABELS:
            amount = effects.get(key, 0)
            if amount == 0:
                continue
            applied[key] = round(self._apply_attribute_delta(player, key, amount))
        return applied

    def _apply_attribute_delta(self, player, key: str, amount: float) -> float:
        attr, maximum_attr = ATTRIBUTE_MAP[key]
        current = float(getattr(player, attr))
        maximum = float(getattr(player, maximum_attr))
        updated = max(0.0, min(maximum, current + amount))
        setattr(player, attr, updated)
        return updated - current

    def _effect_lines(self, effects_applied: dict[str, int]) -> list[str]:
        lines = []
        for key, amount in effects_applied.items():
            if amount == 0:
                continue
            sign = "+" if amount > 0 else ""
            lines.append(f"{sign}{amount} {ATTRIBUTE_LABELS[key]}")
        return lines

    def _failure(self, message: str) -> dict:
        self.message = message
        return {
            "success": False,
            "message": message,
            "effects_applied": {},
            "effect_lines": [],
        }
