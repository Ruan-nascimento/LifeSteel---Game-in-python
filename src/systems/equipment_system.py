from __future__ import annotations

from src.data.items_data import ITEMS
from src.systems.item_system import ITEM_DATABASE, ItemDatabase


class EquipmentSystem:
    def __init__(self, database: ItemDatabase | None = None) -> None:
        self.database = database or ITEM_DATABASE
        self.message = "Equipamento pronto."

    def equip_item(self, player, inventory, item_id: str) -> bool:
        if not self.database.item_exists(item_id) and item_id not in ITEMS:
            self.message = "Item inexistente."
            return False
        data = self.database.normalize_item(item_id) if self.database.item_exists(item_id) else ITEMS.get(item_id)
        if data and data.get("type") not in {"weapon", "tool", "building"}:
            self.message = "Este item nao pode ser equipado."
            return False
        if data and player.level.level < int(data.get("required_level", 1)):
            self.message = "Nivel baixo demais para equipar este item."
            return False
        slot_index = inventory.first_slot_with(item_id)
        if slot_index is None:
            self.message = "Item nao encontrado no inventario."
            return False
        inventory.selected_slot = slot_index
        self.message = f"{data.get('name', item_id) if data else item_id} equipado."
        return True

    def unequip_item(self, player, slot: str = "hand") -> bool:
        if slot == "hand":
            player.inventory.selected_slot = 0
            self.message = "Item desequipado."
            return True
        self.message = "Slot de equipamento desconhecido."
        return False

    def can_use_functionality(self, player, functionality: str) -> bool:
        item = player.equipped_item() if hasattr(player, "equipped_item") else None
        if not item:
            self.message = "Nenhum item equipado."
            return False
        if bool(item.data.get(functionality)):
            return True
        self.message = f"O item equipado nao possui {functionality}."
        return False

    def reduce_durability(self, item_instance, amount: int) -> bool:
        if amount <= 0 or item_instance is None:
            return True
        if getattr(item_instance, "durability", None) is None:
            return True
        item_instance.durability = max(0, int(item_instance.durability) - amount)
        if item_instance.durability <= 0:
            self.message = "Item quebrou."
            return False
        return True
