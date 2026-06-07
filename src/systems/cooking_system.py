from __future__ import annotations

from src.data.food_data import station_allows
from src.data.items_data import ITEMS
from src.data.recipes_data import COOKING_RECIPES


class CookingSystem:
    def __init__(self) -> None:
        self.message = "Cozinha pronta."

    def available_recipes(self, player=None, station_id: str | None = None) -> dict[str, dict]:
        recipes: dict[str, dict] = {}
        for raw_id, recipe in COOKING_RECIPES.items():
            if raw_id not in ITEMS or recipe.get("output") not in ITEMS:
                continue
            if station_id and not station_allows(station_id, recipe.get("required_station")):
                continue
            recipes[raw_id] = recipe
        return dict(sorted(recipes.items(), key=lambda item: ITEMS[item[0]]["name"]))

    def cook(self, player, inventory, item_id: str, station_id: str | None) -> dict:
        recipe = COOKING_RECIPES.get(item_id)
        if not recipe:
            return self._failure("Este item nao pode ser cozido.")
        if not station_allows(station_id, recipe.get("required_station")):
            return self._failure("Estacao errada para esta receita.")

        output_id = recipe.get("output")
        if output_id not in ITEMS:
            return self._failure("Resultado de cozimento inexistente.")
        if not self._has_item(player, inventory, item_id):
            return self._failure("Ingrediente insuficiente.")
        if hasattr(player, "can_receive_item") and not player.can_receive_item(output_id, 1):
            return self._failure("Inventario cheio. Libere espaco antes de cozinhar.")

        if not self._remove_one(player, inventory, item_id):
            return self._failure("Ingrediente insuficiente.")
        leftover = player.add_item(output_id, 1) if hasattr(player, "add_item") else inventory.add_item(output_id, 1)
        if leftover:
            inventory.add_item(item_id, 1)
            return self._failure("Inventario cheio; cozimento cancelado.")

        if hasattr(player, "skills"):
            player.skills.add_xp("Cozinhar", 7)
        item_name = ITEMS[item_id]["name"]
        output_name = ITEMS[output_id]["name"]
        self.message = f"Voce cozinhou {item_name}. Recebeu {output_name}."
        return {
            "success": True,
            "message": self.message,
            "item_id": item_id,
            "output_id": output_id,
        }

    def _has_item(self, player, inventory, item_id: str) -> bool:
        if hasattr(player, "count_item"):
            return player.count_item(item_id) >= 1
        return inventory.count(item_id) >= 1

    def _remove_one(self, player, inventory, item_id: str) -> bool:
        if hasattr(player, "pay_items"):
            return player.pay_items({item_id: 1})
        return inventory.remove_item(item_id, 1)

    def _failure(self, message: str) -> dict:
        self.message = message
        return {"success": False, "message": message}
