from src.data.recipes_data import RECIPES
from src.data.food_data import friendly_station_name, station_allows


class CraftingSystem:
    def __init__(self) -> None:
        self.message = "Receitas prontas."

    def unlocked_recipes(self, player) -> dict:
        unlocked = {}
        for recipe_id, recipe in RECIPES.items():
            level_ok = player.level.level >= recipe.get("required_level", 1)
            skill_name, skill_level = recipe.get("required_skill", ("Sobrevivencia", 1))
            skill_ok = player.skills.level(skill_name) >= skill_level
            if level_ok and skill_ok:
                unlocked[recipe_id] = recipe
        return unlocked

    def station_ok(self, recipe: dict, station_id: str | None) -> bool:
        return station_allows(station_id, recipe.get("required_station"))

    def craft(self, player, recipe_id: str, station_id: str | None = None) -> bool:
        recipe = RECIPES.get(recipe_id)
        if not recipe:
            self.message = "Receita inexistente."
            return False
        if recipe_id not in self.unlocked_recipes(player):
            self.message = "Receita bloqueada."
            return False
        if not self.station_ok(recipe, station_id):
            required = friendly_station_name(recipe.get("required_station"))
            self.message = f"Requer estacao: {required}."
            return False
        ingredients = recipe["ingredients"]
        output_id, amount = recipe["output"]
        if hasattr(player, "can_receive_item") and not player.can_receive_item(output_id, amount):
            self.message = "Inventario cheio. Libere espaco antes de criar."
            return False
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
