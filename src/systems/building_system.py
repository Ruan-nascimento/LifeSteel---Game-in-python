from src.data.recipes_data import RECIPES


BUILDING_COSTS = {
    "campfire": {"wood": 4, "stone": 3},
    "small_chest": {"wood": 12, "fiber": 2},
    "workbench": {"wood": 10, "stone": 4},
    "fence": {"wood": 2},
    "wood_floor": {"wood": 2},
    "simple_wall": {"wood": 3, "fiber": 1},
    "simple_bed": {"wood": 6, "fiber": 4},
    "torch": {"stick": 1, "fiber": 1},
    "small_shelter": {"wood": 24, "stone": 8, "fiber": 8},
    "stone_stove": {"stone": 8, "simple_ore": 2, "wood": 2},
}


BUILDING_LEVELS = {
    "campfire": 1,
    "torch": 1,
    "wood_floor": 1,
    "simple_wall": 1,
    "fence": 1,
    "workbench": 1,
    "small_chest": 1,
    "simple_bed": 2,
    "stone_stove": 1,
    "small_shelter": 5,
}


class BuildingSystem:
    def __init__(self) -> None:
        self.selected_building = "campfire"
        self.message = "Escolha uma construcao."

    def unlocked(self, player) -> list[str]:
        return [
            building
            for building, required_level in BUILDING_LEVELS.items()
            if player.level.level >= required_level
        ]

    def adjusted_cost(self, player, building_id: str) -> dict[str, int]:
        discount = player.skills.building_cost_discount()
        costs = BUILDING_COSTS.get(building_id, {}).copy()
        adjusted = {}
        for item_id, amount in costs.items():
            adjusted[item_id] = max(1, round(amount * (1 - discount)))
        return adjusted

    def can_build(self, player, building_id: str) -> bool:
        costs = self.adjusted_cost(player, building_id)
        can_pay = player.can_pay_items(costs) if hasattr(player, "can_pay_items") else player.inventory.can_pay(costs)
        return building_id in self.unlocked(player) and can_pay

    def build(self, player, world, building_id: str, world_pos) -> bool:
        if building_id not in self.unlocked(player):
            self.message = "Construcao bloqueada por level."
            return False
        tile = world.pixel_to_tile(world_pos)
        if not world.can_place_structure(tile):
            self.message = "Local invalido para construir."
            return False
        costs = self.adjusted_cost(player, building_id)
        paid = player.pay_items(costs) if hasattr(player, "pay_items") else player.inventory.pay(costs)
        if not paid:
            self.message = "Materiais insuficientes."
            return False
        world.add_structure(building_id, tile)
        player.skills.add_xp("Construcao", 8)
        player.skills.add_xp("Sobrevivencia", 3)
        self.message = f"Construiu {building_id}."
        return True
