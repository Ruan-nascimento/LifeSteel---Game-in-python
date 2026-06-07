from src.data.food_data import food_cooking_recipes, food_crafting_recipes


RECIPES = {
    "stone_axe": {
        "name": "Machado de Pedra",
        "ingredients": {"wood": 3, "stone": 2, "fiber": 1},
        "output": ("stone_axe", 1),
        "required_level": 1,
        "required_skill": ("Lenhador", 1),
    },
    "stone_pickaxe": {
        "name": "Picareta de Pedra",
        "ingredients": {"wood": 3, "stone": 3},
        "output": ("stone_pickaxe", 1),
        "required_level": 1,
        "required_skill": ("Mineracao", 1),
    },
    "torch": {
        "name": "Tocha",
        "ingredients": {"stick": 1, "fiber": 1},
        "output": ("torch", 2),
        "required_level": 1,
        "required_skill": ("Sobrevivencia", 1),
    },
    "campfire": {
        "name": "Fogueira",
        "ingredients": {"wood": 4, "stone": 3},
        "output": ("campfire", 1),
        "required_level": 1,
        "required_skill": ("Sobrevivencia", 1),
    },
    "workbench": {
        "name": "Bancada de Trabalho",
        "ingredients": {"wood": 10, "stone": 4},
        "output": ("workbench", 1),
        "required_level": 1,
        "required_skill": ("Construcao", 1),
    },
    "stone_stove": {
        "name": "Fogao de Pedra",
        "ingredients": {"stone": 8, "simple_ore": 2, "wood": 2},
        "output": ("stone_stove", 1),
        "required_level": 1,
        "required_skill": ("Construcao", 1),
    },
    "small_chest": {
        "name": "Bau Pequeno",
        "ingredients": {"wood": 12, "fiber": 2},
        "output": ("small_chest", 1),
        "required_level": 1,
        "required_skill": ("Construcao", 1),
    },
    "small_health_potion": {
        "name": "Pocao Pequena de Vida",
        "ingredients": {"herb": 2, "mushroom": 1},
        "output": ("small_health_potion", 1),
        "required_level": 1,
        "required_skill": ("Alquimia", 1),
    },
}


RECIPES.update(food_crafting_recipes())


COOKING_RECIPES = {
    "raw_pork": {"output": "cooked_pork", "time": 4, "label": "Assar carne de porco"},
    "raw_beef": {"output": "cooked_beef", "time": 5, "label": "Assar bife"},
    "raw_chicken": {"output": "cooked_chicken", "time": 3, "label": "Assar frango"},
    "small_fish": {"output": "cooked_fish", "time": 3, "label": "Assar peixe"},
    "raw_meat": {"output": "cooked_beef", "time": 4, "label": "Assar carne comum"},
}


COOKING_RECIPES.update(food_cooking_recipes())
