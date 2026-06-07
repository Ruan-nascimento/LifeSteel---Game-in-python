from __future__ import annotations

from src.systems.item_system import ITEM_DATABASE, ItemDatabase


class UpgradeSystem:
    def __init__(self, database: ItemDatabase | None = None) -> None:
        self.database = database or ITEM_DATABASE
        self.message = "Melhorias prontas."

    def apply_upgrade(self, player, inventory, item_id: str) -> dict:
        if not self.database.item_exists(item_id):
            return self._failure("Melhoria inexistente.")
        data = self.database.normalize_item(item_id)
        if data.get("type") != "upgrade":
            return self._failure("Este item nao e uma melhoria.")
        if player.level.level < int(data.get("required_level", 1)):
            return self._failure("Nivel baixo demais para usar esta melhoria.")
        if item_id in getattr(player, "upgrades_applied", set()):
            return self._failure("Esta melhoria ja foi aplicada.")
        if not inventory.has_item(item_id, 1):
            return self._failure("Melhoria nao encontrada no inventario.")

        functionalities = data.get("functionalities") or data
        if functionalities.get("adds_inventory_slots"):
            bonus = int(functionalities.get("slot_bonus", 0))
            if bonus > 0:
                player.inventory.capacity += bonus
                player.inventory.slots.extend([None for _ in range(bonus)])
        if functionalities.get("consumed_on_use", True):
            inventory.remove_item(item_id, 1)

        if not hasattr(player, "upgrades_applied"):
            player.upgrades_applied = set()
        player.upgrades_applied.add(item_id)
        self.message = f"Voce usou {data.get('name', item_id)}."
        return {"success": True, "message": self.message, "item_id": item_id}

    def _failure(self, message: str) -> dict:
        self.message = message
        return {"success": False, "message": message}
