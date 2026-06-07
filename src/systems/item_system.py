from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from src.core.json_loader import load_json


ITEM_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "items.json"

JSON_TO_LEGACY_ALIASES = {
    "wooden_sword": "wood_sword",
    "training_dagger": "simple_dagger",
    "cracked_staff": "broken_staff",
    "wooden_baton": "simple_staff",
    "hunters_bow": "simple_bow",
    "basic_fishing_rod": "simple_fishing_rod",
    "basic_workbench": "workbench",
    "campfire_item": "campfire",
    "stone_furnace_item": "stone_stove",
}

STATION_ALIASES = {
    "workbench_basic": "workbench",
    "basic_workbench": "workbench",
    "campfire_basic": "campfire",
    "campfire_item": "campfire",
    "stone_furnace": "stone_stove",
    "stone_furnace_item": "stone_stove",
    "iron_stove": "stone_stove",
}

DISPLAY_CATEGORIES = {
    "weapon": "Armas",
    "tool": "Ferramentas",
    "food": "Comida",
    "material": "Materiais",
    "book": "Livros",
    "utility": "Utilitarios",
    "station": "Construcoes",
    "building": "Construcoes",
    "upgrade": "Melhorias",
}

TYPE_COLORS = {
    "weapon": (184, 92, 64),
    "tool": (138, 128, 102),
    "book": (164, 117, 77),
    "utility": (91, 150, 178),
    "station": (122, 86, 52),
    "building": (122, 86, 52),
    "upgrade": (196, 154, 70),
    "material": (136, 122, 96),
}


def normalize_station_id(station_id: str | None) -> str | None:
    if not station_id:
        return None
    return STATION_ALIASES.get(station_id, station_id)


def normalize_skill_name(skill_id: str | None) -> str:
    if not skill_id:
        return "Sobrevivencia"
    mapping = {
        "comunicacao": "Comunicacao",
        "cozinhar": "Cozinhar",
        "pescar": "Pescar",
        "lenhador": "Lenhador",
        "namorador": "Namorador",
        "magia": "Magia",
        "construcao": "Construcao",
        "politica": "Politica",
        "mineracao": "Mineracao",
        "agricultura": "Agricultura",
        "combate": "Combate",
        "comercio": "Comercio",
        "sobrevivencia": "Sobrevivencia",
        "alquimia": "Alquimia",
        "caca": "Caca",
    }
    return mapping.get(skill_id.lower(), skill_id.replace("_", " ").title())


class ItemDatabase:
    def __init__(self, json_path: str | Path = ITEM_DATA_PATH) -> None:
        self.json_path = Path(json_path)
        self.data = load_json(self.json_path, default={})
        self.items = self.index_items_by_id()
        self.vendors = {
            vendor["id"]: vendor
            for vendor in self.data.get("shop_vendors", [])
            if vendor.get("id")
        }
        self.cooking_data = self.data.get("cooking_system", {})
        self._validate_unique_ids()

    def index_items_by_id(self) -> dict[str, dict]:
        return {
            item["id"]: deepcopy(item)
            for item in self.data.get("items", [])
            if item.get("id")
        }

    def _validate_unique_ids(self) -> None:
        ids = [item.get("id") for item in self.data.get("items", []) if item.get("id")]
        duplicates = sorted({item_id for item_id in ids if ids.count(item_id) > 1})
        if duplicates:
            raise ValueError(f"Duplicate item ids in {self.json_path}: {', '.join(duplicates)}")

    def canonical_id(self, item_id: str) -> str:
        if item_id in self.items:
            return item_id
        for json_id, legacy_id in JSON_TO_LEGACY_ALIASES.items():
            if legacy_id == item_id and json_id in self.items:
                return json_id
        return item_id

    def get_item(self, item_id: str) -> dict:
        canonical = self.canonical_id(item_id)
        if canonical not in self.items:
            raise KeyError(f"Item not found: {item_id}")
        return deepcopy(self.items[canonical])

    def item_exists(self, item_id: str) -> bool:
        return self.canonical_id(item_id) in self.items

    def get_items_by_type(self, item_type: str) -> list[dict]:
        return [deepcopy(item) for item in self.items.values() if item.get("type") == item_type]

    def get_items_by_category(self, category: str) -> list[dict]:
        return [deepcopy(item) for item in self.items.values() if item.get("category") == category]

    def get_items_by_level(self, level: int) -> list[dict]:
        return [deepcopy(item) for item in self.items.values() if int(item.get("required_level", 1)) <= level]

    def get_buyable_items(self, vendor_id: str | None, player_level: int) -> list[dict]:
        vendor = self.vendors.get(vendor_id or "vendor_milo_root")
        categories = set(vendor.get("categories_sold", [])) if vendor else set()
        result = []
        for item in self.items.values():
            if not item.get("buyable"):
                continue
            if categories and item.get("type") not in categories:
                continue
            entry = deepcopy(item)
            entry["locked"] = player_level < int(item.get("required_level", 1))
            result.append(entry)
        return sorted(result, key=lambda item: (item.get("required_level", 1), item.get("name", item["id"])))

    def get_sellable_items(self) -> list[dict]:
        return [deepcopy(item) for item in self.items.values() if item.get("sellable")]

    def get_vendor(self, vendor_id: str = "vendor_milo_root") -> dict | None:
        vendor = self.vendors.get(vendor_id)
        return deepcopy(vendor) if vendor else None

    def normalize_item(self, item_id: str, item: dict | None = None) -> dict:
        raw = deepcopy(item or self.get_item(item_id))
        raw_id = raw.get("id", item_id)
        item_type = raw.get("type", "material")
        stats = raw.get("stats") or {}
        functionalities = raw.get("functionalities") or {}
        effects = raw.get("effects") or {}
        normalized = deepcopy(raw)

        normalized["source"] = "items.json"
        normalized["name"] = raw.get("name", raw_id)
        normalized["description"] = raw.get("description", "")
        normalized["required_level"] = int(raw.get("required_level", 1))
        normalized["rarity"] = raw.get("rarity", "common")
        normalized["category"] = DISPLAY_CATEGORIES.get(item_type, raw.get("category", item_type.title()))
        normalized["price"] = int(raw.get("buy_price", raw.get("price", 0)) or 0)
        normalized["buy_price"] = int(raw.get("buy_price", normalized["price"]) or 0)
        normalized["sell_price"] = int(raw.get("sell_price", max(1, normalized["price"] // 2)) or 0)
        normalized["stackable"] = bool(raw.get("stackable", item_type in {"food", "drink", "material"}))
        normalized["max_stack"] = int(raw.get("max_stack", 99 if normalized["stackable"] else 1))
        normalized["icon_color"] = tuple(raw.get("icon_color", TYPE_COLORS.get(item_type, (235, 235, 235))))

        for key, value in stats.items():
            normalized.setdefault(key, value)
        for key, value in functionalities.items():
            normalized.setdefault(key, value)
        for key, value in effects.items():
            normalized.setdefault(key, value)

        if item_type == "station":
            normalized["type"] = "building"
            station_id = raw.get("functionalities", {}).get("station_id") or raw.get("station_id") or raw_id
            normalized["station_id"] = normalize_station_id(station_id)
            normalized["building"] = normalized["station_id"]
            normalized["stackable"] = True
            normalized["max_stack"] = int(raw.get("max_stack", 5))
        elif item_type == "upgrade":
            normalized["type"] = "upgrade"
            normalized["stackable"] = False
            normalized["max_stack"] = 1

        if raw.get("category") and item_type == "tool":
            normalized["tool_type"] = raw["category"]
        elif raw.get("category") in {"axe", "pickaxe", "shovel", "hoe", "fishing_rod"}:
            normalized["tool_type"] = raw["category"]

        recipe = self.recipe_for(raw_id)
        if recipe:
            normalized["recipe"] = recipe
        return normalized

    def recipe_for(self, item_id: str) -> dict | None:
        raw = self.items.get(self.canonical_id(item_id))
        if not raw or not raw.get("craftable") or not raw.get("recipe"):
            return None
        recipe = deepcopy(raw["recipe"])
        ingredients = {
            ingredient["id"]: int(ingredient.get("quantity", 1))
            for ingredient in recipe.get("ingredients", [])
            if ingredient.get("id")
        }
        skill_data = recipe.get("required_skill") or {}
        skill_name = normalize_skill_name(skill_data.get("skill")) if isinstance(skill_data, dict) else "Sobrevivencia"
        skill_level = int(skill_data.get("level", 1)) if isinstance(skill_data, dict) else 1
        return {
            "id": raw["id"],
            "name": raw.get("name", raw["id"]),
            "ingredients": ingredients,
            "output": (raw["id"], int(recipe.get("output_quantity", 1))),
            "required_level": int(raw.get("required_level", 1)),
            "required_station": normalize_station_id(recipe.get("required_station")),
            "required_skill": (skill_name, skill_level),
            "required_skill_data": {"skill": skill_name, "level": skill_level},
            "xp_skill": skill_name,
            "xp": 8 + int(raw.get("required_level", 1)) * 2,
            "source": "items.json",
        }

    def craftable_recipes(self) -> dict[str, dict]:
        recipes = {}
        for item_id in self.items:
            recipe = self.recipe_for(item_id)
            if recipe:
                recipes[item_id] = recipe
                legacy_id = JSON_TO_LEGACY_ALIASES.get(item_id)
                if legacy_id:
                    legacy_recipe = deepcopy(recipe)
                    legacy_recipe["id"] = legacy_id
                    legacy_recipe["output"] = (legacy_id, recipe["output"][1])
                    recipes[legacy_id] = legacy_recipe
        return recipes

    def export_legacy_items(self) -> dict[str, dict]:
        result = {}
        for item_id, raw in self.items.items():
            normalized = self.normalize_item(item_id, raw)
            result[item_id] = normalized
            legacy_id = JSON_TO_LEGACY_ALIASES.get(item_id)
            if legacy_id:
                alias = deepcopy(normalized)
                alias["id"] = legacy_id
                result[legacy_id] = alias
        return result


class ItemSystem:
    def __init__(self, database: ItemDatabase | None = None) -> None:
        self.database = database or ITEM_DATABASE
        self.message = "Sistema de itens pronto."

    def get_item(self, item_id: str) -> dict | None:
        try:
            return self.database.get_item(item_id)
        except KeyError:
            self.message = f"Item inexistente: {item_id}."
            return None

    def can_use(self, player, item_id: str) -> bool:
        item = self.get_item(item_id)
        if not item:
            return False
        if getattr(player, "level", None) and player.level.level < int(item.get("required_level", 1)):
            self.message = "Seu nivel ainda e baixo demais para usar este item."
            return False
        return True

    def use_item(self, player, inventory, item_id: str, slot_index: int | None = None) -> dict:
        from src.items.item import make_item
        from src.systems.reading_system import ReadingSystem
        from src.systems.upgrade_system import UpgradeSystem

        data = self.database.normalize_item(item_id) if self.database.item_exists(item_id) else None
        if not data:
            return self._failure("Item inexistente.")
        item_type = data.get("type")
        if item_type == "book":
            return ReadingSystem(self.database).start_reading(player, inventory, item_id)
        if item_type == "upgrade":
            return UpgradeSystem(self.database).apply_upgrade(player, inventory, item_id)
        item = make_item(item_id)
        if item.is_consumable() and slot_index is not None:
            from src.systems.consumable_system import ConsumableSystem

            return ConsumableSystem().consume(player, inventory, item_id, slot_index)
        self.message = "Item equipado."
        return {"success": True, "message": self.message}

    def _failure(self, message: str) -> dict:
        self.message = message
        return {"success": False, "message": message}


ITEM_DATABASE = ItemDatabase()
