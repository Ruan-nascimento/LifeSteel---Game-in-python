from __future__ import annotations

from src.core.json_loader import load_json
from src.core.settings import BASE_DIR
from src.data.items_data import ITEMS


DURABILITY_RULES_PATH = BASE_DIR / "src" / "data" / "durability_rules.json"


class DurabilitySystem:
    def __init__(self, data_path=DURABILITY_RULES_PATH) -> None:
        self.rules = load_json(data_path, {"materials": {}, "usage_damage": {}, "tool_targets": {}})
        self.magic_cast_counter = 0

    def max_durability(self, item_id: str) -> int | None:
        data = ITEMS.get(item_id, {})
        if data.get("max_durability") or data.get("durability"):
            return int(data.get("max_durability", data.get("durability")))
        if data.get("type") not in {"weapon", "tool"}:
            return None
        material = self._infer_material(item_id, data)
        return int(self.rules.get("materials", {}).get(material, {}).get("default_durability", 60))

    def initialize_slot(self, slot) -> None:
        maximum = self.max_durability(slot.item_id)
        if not maximum:
            return
        slot.instance_id = slot.instance_id or f"item_{id(slot):x}"
        slot.durability = maximum if slot.durability is None else min(int(slot.durability), maximum)

    def apply_selected_use_damage(self, player, action_type: str, target_type: str, notifications=None, correct: bool | None = None) -> bool:
        slot = player.inventory.selected()
        if not slot:
            return False
        return self.apply_use_damage(player, slot, action_type, target_type, notifications, correct)

    def apply_use_damage(self, player, item_instance, action_type: str, target_type: str, notifications=None, correct: bool | None = None) -> bool:
        maximum = self.max_durability(item_instance.item_id)
        if maximum is None:
            return False
        self.initialize_slot(item_instance)
        item_data = ITEMS.get(item_instance.item_id, {})
        correct_tool = self.is_correct_tool(item_data, action_type, target_type) if correct is None else correct
        usage = self.rules.get("usage_damage", {})
        if action_type == "magic":
            self.magic_cast_counter += 1
            if self.magic_cast_counter < int(usage.get("magic_cast_interval", 3)):
                return False
            self.magic_cast_counter = 0
            damage = 1
        elif action_type == "combat" and item_data.get("type") == "tool":
            damage = int(usage.get("tool_as_weapon", 2))
        elif action_type == "combat":
            damage = int(usage.get("weapon_attack", 1))
        else:
            damage = int(usage.get("correct_tool" if correct_tool else "wrong_tool", 1 if correct_tool else 3))
        item_instance.durability = max(0, int(item_instance.durability or maximum) - damage)
        if not correct_tool and notifications:
            notifications.push(f"{item_data.get('name', item_instance.item_id)} nao e adequado para isso.")
        if item_instance.durability <= 0:
            self.break_item(player, item_instance, notifications)
            return True
        return False

    def is_correct_tool(self, item_data: dict, action_type: str, target_type: str) -> bool:
        if action_type == "combat":
            return item_data.get("type") == "weapon" or target_type in {"enemy", "animal"}
        if action_type == "magic":
            return item_data.get("tool_type") in {"staff", "wand"} or item_data.get("damage_type") == "magico"
        tool_type = item_data.get("tool_type")
        if not tool_type:
            if "sword" in item_data.get("id", ""):
                tool_type = "sword"
            return False
        targets = set(self.rules.get("tool_targets", {}).get(tool_type, []))
        return target_type in targets

    def break_item(self, player, item_instance, notifications=None) -> None:
        for index, slot in enumerate(player.inventory.slots):
            if slot is item_instance:
                player.inventory.slots[index] = None
                if player.inventory.selected_slot == index:
                    player.equipped_items["hand"] = None
                if notifications:
                    notifications.push(f"Seu {ITEMS[item_instance.item_id]['name']} quebrou.")
                return
        backpack = player.backpack_contents()
        if backpack is not None:
            for index, slot in enumerate(backpack):
                if slot is item_instance:
                    backpack[index] = None
                    if notifications:
                        notifications.push(f"Seu {ITEMS[item_instance.item_id]['name']} quebrou.")
                    return

    def get_tooltip_text(self, item_instance) -> list[str]:
        maximum = self.max_durability(item_instance.item_id)
        if not maximum:
            return []
        current = maximum if item_instance.durability is None else int(item_instance.durability)
        ratio = current / max(1, maximum)
        state = "Bom"
        if ratio <= 0.10:
            state = "Muito danificado"
        elif ratio <= 0.25:
            state = "Quase quebrando"
        return [f"Durabilidade: {current}/{maximum}", f"Estado: {int(ratio * 100)}% - {state}"]

    def _infer_material(self, item_id: str, data: dict) -> str:
        rarity = str(data.get("rarity", ""))
        if rarity in {"rare", "epic", "legendary", "unique"}:
            return "rare" if rarity == "rare" else "unique"
        for material in ("wood", "stone", "copper", "iron", "crystal"):
            if material in item_id:
                return material
        if "varinha" in item_id or "wand" in item_id:
            return "crystal"
        return "stone"
