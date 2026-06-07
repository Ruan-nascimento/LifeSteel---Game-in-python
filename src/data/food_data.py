from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


DATA_PATH = Path(__file__).with_name("foods.json")

CONSUMABLE_TYPES = {"food", "drink", "potion"}

SKILL_NAMES = {
    "cozinhar": "Cozinhar",
    "alquimia": "Alquimia",
}

STATION_NAMES = {
    "campfire": "Fogueira",
    "campfire_basic": "Fogueira",
    "campfire_item": "Fogueira",
    "stone_stove": "Fogao de Pedra",
    "stone_furnace": "Fornalha de Pedra",
    "stone_furnace_item": "Fornalha de Pedra",
    "workbench": "Bancada de Trabalho",
    "workbench_basic": "Bancada de Trabalho",
    "basic_workbench": "Bancada de Trabalho",
    "panela": "Panela",
    "fogao": "Fogao",
    "fogao_avancado": "Fogao Avancado",
    "espremedor": "Espremedor",
    "mesa_de_preparo": "Mesa de Preparo",
    "caldeirao_simples": "Caldeirao Simples",
    "caldeirao_alquimico": "Caldeirao Alquimico",
    "caldeirao_lendario": "Caldeirao Lendario",
}

STATION_COMPATIBILITY = {
    "campfire": {"campfire", "campfire_basic", "campfire_item", "fogueira"},
    "stone_stove": {
        "campfire",
        "campfire_basic",
        "campfire_item",
        "fogueira",
        "stone_stove",
        "stone_furnace",
        "stone_furnace_item",
        "fogao",
        "panela",
        "fogao_avancado",
        "espremedor",
        "mesa_de_preparo",
        "caldeirao_simples",
        "caldeirao_alquimico",
        "caldeirao_lendario",
    },
    "workbench": {"workbench", "workbench_basic", "basic_workbench", "mesa_de_preparo"},
}

CATEGORY_LABELS = {
    "raw_meat": "Comida",
    "cooked_meat": "Comida",
    "fruit": "Comida",
    "magical_fruit": "Comida",
    "raw_fish": "Comida",
    "cooked_fish": "Comida",
    "meal": "Comida",
    "legendary_meal": "Comida",
    "juice": "Bebidas",
    "magical_drink": "Bebidas",
    "health_potion": "Pocoes",
    "mana_potion": "Pocoes",
    "hybrid_potion": "Pocoes",
    "energy_potion": "Pocoes",
    "premium_potion": "Pocoes",
}

TYPE_COLORS = {
    "food": (211, 112, 76),
    "drink": (74, 166, 218),
    "potion": (158, 91, 218),
}

RARITY_STOCK = {
    "common": 18,
    "uncommon": 10,
    "rare": 5,
    "epic": 2,
    "legendary": 1,
}

RARITY_PRICE_MULTIPLIER = {
    "common": 1.0,
    "uncommon": 1.12,
    "rare": 1.35,
    "epic": 1.75,
    "legendary": 2.35,
}

INGREDIENT_ALIASES = {
    "clean_water": "water_cup",
    "crystal_water": "water_flask",
    "red_herb": "herb",
    "blue_herb": "herb",
    "yellow_herb": "herb",
    "rare_herb": "herb",
    "wild_leaf": "fiber",
    "crystal_salt": "stone",
    "carrot": "basic_seed",
    "potato": "mushroom",
    "rice": "basic_seed",
    "bean": "basic_seed",
    "moon_sugar": "mushroom",
    "phoenix_feather": "feather",
    "golden_carrot": "basic_seed",
}

SOURCE_ALIASES = {
    "tree": {"arvore comum", "árvore comum"},
    "bush": {"arbusto de frutas", "arbusto arcano"},
    "pig": {"porco selvagem", "javali"},
    "cow": {"vaca selvagem"},
    "chicken": {"galinha", "ave selvagem"},
    "chest": {"bau simples", "baú simples"},
    "hunter_chest": {"bau de cacador", "baú de caçador"},
    "river": {"pesca em rio"},
}


@lru_cache(maxsize=1)
def load_food_database() -> dict:
    with DATA_PATH.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def foods_by_id() -> dict[str, dict]:
    return {
        food["id"]: food
        for food in load_food_database().get("foods", [])
        if food.get("id")
    }


def friendly_station_name(station_id: str | None) -> str:
    if not station_id:
        return "Qualquer estacao"
    return STATION_NAMES.get(station_id, station_id.replace("_", " ").title())


def normalize_skill(skill_id: str | None) -> str:
    if not skill_id:
        return "Sobrevivencia"
    return SKILL_NAMES.get(skill_id.lower(), skill_id.replace("_", " ").title())


def station_allows(station_id: str | None, required_station: str | None) -> bool:
    if not required_station:
        return True
    if not station_id:
        return False
    if station_id == required_station:
        return True
    return required_station in STATION_COMPATIBILITY.get(station_id, set())


def _item_color(food: dict) -> tuple[int, int, int]:
    category = food.get("category", "")
    if "fruit" in category:
        return (216, 76, 83)
    if "fish" in category:
        return (91, 169, 190)
    if "meat" in category:
        return (181, 85, 65)
    if "juice" in category or food.get("type") == "drink":
        return (76, 175, 220)
    if food.get("type") == "potion":
        return (158, 91, 218)
    return TYPE_COLORS.get(food.get("type", "food"), (230, 220, 180))


def _display_category(food: dict) -> str:
    return CATEGORY_LABELS.get(food.get("category", ""), "Comida")


def _fallback_price(food: dict) -> int:
    shop = food.get("shop") or {}
    if food.get("buyable") and shop.get("price"):
        return int(shop["price"])
    sell_price = int(food.get("sell_price", 1))
    rarity = food.get("rarity", "common")
    return max(1, round(sell_price * 2 * RARITY_PRICE_MULTIPLIER.get(rarity, 1.0)))


def _to_item(food: dict) -> dict:
    effects = dict(food.get("effects") or {})
    item = {
        "name": food.get("name", food["id"]),
        "type": food.get("type", "food"),
        "category": _display_category(food),
        "food_category": food.get("category", ""),
        "description": food.get("description", ""),
        "price": _fallback_price(food),
        "sell_price": int(food.get("sell_price", max(1, _fallback_price(food) // 2))),
        "stackable": bool(food.get("stackable", True)),
        "max_stack": int(food.get("max_stack", 20)),
        "rarity": food.get("rarity", "common"),
        "effects": effects,
        "drop": food.get("drop"),
        "buyable": bool(food.get("buyable", False)),
        "shop": food.get("shop"),
        "craftable": bool(food.get("craftable", False)),
        "recipe": food.get("recipe"),
        "cookable": bool(food.get("cookable", False)),
        "cooks_into": food.get("cooks_into"),
        "special_effects": food.get("special_effects", []),
        "icon_color": _item_color(food),
        "source": "foods.json",
    }
    if "health" in effects:
        item["heal"] = effects["health"]
    for key in ("hunger", "thirst", "energy", "mana", "mana_percent"):
        if key in effects:
            item[key] = effects[key]
    return item


@lru_cache(maxsize=1)
def food_items() -> dict[str, dict]:
    return {food_id: _to_item(food) for food_id, food in foods_by_id().items()}


def missing_ingredient_items(existing_item_ids: set[str]) -> dict[str, dict]:
    missing: dict[str, dict] = {}
    for food in foods_by_id().values():
        recipe = food.get("recipe") or {}
        for ingredient in recipe.get("ingredients") or []:
            item_id = INGREDIENT_ALIASES.get(ingredient.get("id"), ingredient.get("id"))
            if not item_id or item_id in existing_item_ids or item_id in missing:
                continue
            missing[item_id] = {
                "name": item_id.replace("_", " ").title(),
                "type": "material",
                "category": "Ingredientes",
                "description": "Ingrediente preparado para receitas futuras do JSON de alimentos.",
                "price": 8,
                "sell_price": 3,
                "stackable": True,
                "max_stack": 50,
                "rarity": "common",
                "icon_color": (180, 150, 96),
                "source": "foods.json_placeholder",
            }
    return missing


def food_crafting_recipes() -> dict[str, dict]:
    recipes: dict[str, dict] = {}
    for item_id, food in foods_by_id().items():
        if not food.get("craftable") or not food.get("recipe"):
            continue
        recipe = food["recipe"]
        required_skill = recipe.get("required_skill") or {}
        skill_name = normalize_skill(required_skill.get("skill"))
        skill_level = int(required_skill.get("level", 1))
        ingredients: dict[str, int] = {}
        for ingredient in recipe.get("ingredients", []):
            if not ingredient.get("id"):
                continue
            ingredient_id = INGREDIENT_ALIASES.get(ingredient["id"], ingredient["id"])
            ingredients[ingredient_id] = ingredients.get(ingredient_id, 0) + int(ingredient.get("quantity", 1))
        recipes[item_id] = {
            "name": food.get("name", item_id),
            "ingredients": ingredients,
            "output": (item_id, 1),
            "required_level": skill_level,
            "required_skill": (skill_name, skill_level),
            "required_station": recipe.get("required_station"),
            "xp_skill": skill_name,
            "xp": 12 if skill_name == "Cozinhar" else 10,
            "source": "foods.json",
        }
    return recipes


def food_cooking_recipes() -> dict[str, dict]:
    recipes: dict[str, dict] = {}
    for item_id, food in foods_by_id().items():
        if not food.get("cookable") or not food.get("cooks_into"):
            continue
        recipes[item_id] = {
            "output": food["cooks_into"],
            "time": 4,
            "label": f"Preparar {food.get('name', item_id)}",
            "required_station": "campfire",
            "source": "foods.json",
        }
    return recipes


def food_shop_stock() -> list[dict]:
    stock: list[dict] = []
    for item_id, food in foods_by_id().items():
        if not food.get("buyable"):
            continue
        shop = food.get("shop") or {}
        rarity = food.get("rarity", "common")
        stock.append(
            {
                "id": item_id,
                "price": int(shop.get("price", _fallback_price(food))),
                "required_level": int(shop.get("required_level", 1)),
                "stock": RARITY_STOCK.get(rarity, 8),
                "seller": shop.get("seller", "vendedor geral"),
                "only_buyable": bool(shop.get("only_buyable", False)),
            }
        )
    return stock


def drop_sources() -> dict[str, list[dict]]:
    sources: dict[str, list[dict]] = {}
    for item_id, food in foods_by_id().items():
        drop = food.get("drop") or {}
        for source in drop.get("source") or []:
            normalized = source.lower()
            sources.setdefault(normalized, []).append({"item_id": item_id, "rarity": food.get("rarity", "common"), **drop})
    return sources


def source_terms(source_id: str) -> set[str]:
    normalized = source_id.lower()
    return {normalized, *SOURCE_ALIASES.get(normalized, set())}
