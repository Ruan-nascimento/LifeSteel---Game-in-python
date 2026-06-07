from copy import deepcopy

from src.data.recipes_data import RECIPES
from src.data.food_data import friendly_station_name, station_allows
from src.systems.item_system import ITEM_DATABASE


class CraftingSystem:
    def __init__(self) -> None:
        self.message = "Receitas prontas."
        self.recipes = self._load_recipes()

    def _load_recipes(self) -> dict:
        recipes = deepcopy(RECIPES)
        for recipe_id, recipe in ITEM_DATABASE.craftable_recipes().items():
            recipes[recipe_id] = recipe
        return recipes

    def unlocked_recipes(self, player) -> dict:
        unlocked = {}
        for recipe_id, recipe in self.recipes.items():
            level_ok = player.level.level >= recipe.get("required_level", 1)
            skill_name, skill_level = recipe.get("required_skill", ("Sobrevivencia", 1))
            skill_ok = player.skills.level(skill_name) >= skill_level
            if level_ok and skill_ok:
                unlocked[recipe_id] = recipe
        return unlocked

    def station_ok(self, recipe: dict, station_id: str | None) -> bool:
        return station_allows(station_id, recipe.get("required_station"))

    def get_missing_ingredients(self, inventory, recipe: dict) -> dict[str, int]:
        missing: dict[str, int] = {}
        for item_id, needed in recipe.get("ingredients", {}).items():
            owned = inventory.count(item_id)
            if owned < needed:
                missing[item_id] = needed - owned
        return missing

    def consume_ingredients(self, inventory, recipe: dict) -> bool:
        costs = recipe.get("ingredients", {})
        if not inventory.can_pay(costs):
            return False
        return inventory.pay(costs)

    def can_craft(self, player, inventory, item_id: str, station_id: str | None = None) -> tuple[bool, str]:
        recipe = self.recipes.get(item_id)
        if not recipe:
            return False, "Receita inexistente."
        if item_id not in self.unlocked_recipes(player):
            return False, "Receita bloqueada."
        if not self.station_ok(recipe, station_id):
            required = friendly_station_name(recipe.get("required_station"))
            return False, f"Voce precisa de {required}."
        skill_name, skill_level = recipe.get("required_skill", ("Sobrevivencia", 1))
        if player.skills.level(skill_name) < skill_level:
            return False, f"Seu nivel de {skill_name} e baixo demais."
        missing = {}
        for ingredient_id, needed in recipe.get("ingredients", {}).items():
            owned = player.count_item(ingredient_id) if hasattr(player, "count_item") else inventory.count(ingredient_id)
            if owned < needed:
                missing[ingredient_id] = needed - owned
        if missing:
            item_id_missing = next(iter(missing))
            return False, f"Voce nao possui {item_id_missing} suficiente."
        output_id, amount = recipe["output"]
        if hasattr(player, "can_receive_item") and not player.can_receive_item(output_id, amount):
            return False, "Inventario cheio."
        if not hasattr(player, "can_receive_item") and not inventory.can_accept_item(output_id, amount):
            return False, "Inventario cheio."
        return True, "Pode criar."

    def craft(self, player, recipe_id: str, station_id: str | None = None) -> bool:
        recipe = self.recipes.get(recipe_id)
        if not recipe:
            self.message = "Receita inexistente."
            return False
        can_make, reason = self.can_craft(player, player.inventory, recipe_id, station_id)
        if not can_make:
            self.message = reason
            return False
        ingredients = recipe["ingredients"]
        output_id, amount = recipe["output"]
        if hasattr(player, "pay_items"):
            paid = player.pay_items(ingredients)
        else:
            paid = player.inventory.pay(ingredients)
        if not paid:
            self.message = "Materiais insuficientes."
            return False
        leftover = player.add_item(output_id, amount) if hasattr(player, "add_item") else player.inventory.add_item(output_id, amount)
        if leftover:
            self.message = "Inventario cheio; crafting cancelado."
            for item_id, qty in ingredients.items():
                if hasattr(player, "add_item"):
                    player.add_item(item_id, qty)
                else:
                    player.inventory.add_item(item_id, qty)
            return False
        xp_skill = recipe.get("xp_skill")
        if xp_skill:
            player.skills.add_xp(xp_skill, int(recipe.get("xp", 8)))
        else:
            player.skills.add_xp("Construcao", 4)
            player.skills.add_xp("Sobrevivencia", 3)
        self.message = f"Criou {recipe['name']}."
        return True
