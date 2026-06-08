from src.core.json_loader import load_json
from src.core.settings import BASE_DIR


ENEMY_TYPES = {
    "forest_slime": {
        "name": "Slime da Floresta",
        "biome": "floresta",
        "base_hp": 28,
        "hp_per_level": 9,
        "base_damage": 5,
        "damage_per_level": 2,
        "speed": 70,
        "aggro_range": 210,
        "attack_range": 34,
        "ranged": False,
        "fragile": False,
        "color": (67, 178, 91),
        "xp": 14,
        "coins": 6,
        "drops": {"fiber": (0.35, 1, 2), "herb": (0.18, 1, 1)},
    },
    "young_wolf": {
        "name": "Lobo Jovem",
        "biome": "floresta",
        "base_hp": 34,
        "hp_per_level": 11,
        "base_damage": 7,
        "damage_per_level": 3,
        "speed": 102,
        "aggro_range": 250,
        "attack_range": 36,
        "ranged": False,
        "fragile": False,
        "color": (119, 121, 111),
        "xp": 18,
        "coins": 8,
        "drops": {"raw_meat": (0.55, 1, 1), "hide": (0.22, 1, 1)},
    },
    "forest_bat": {
        "name": "Morcego",
        "biome": "floresta",
        "base_hp": 22,
        "hp_per_level": 7,
        "base_damage": 5,
        "damage_per_level": 2,
        "speed": 124,
        "aggro_range": 230,
        "attack_range": 32,
        "ranged": False,
        "fragile": True,
        "color": (86, 72, 105),
        "xp": 13,
        "coins": 5,
        "drops": {"fiber": (0.25, 1, 1)},
    },
    "thorn_plant": {
        "name": "Planta Espinhosa",
        "biome": "floresta",
        "base_hp": 24,
        "hp_per_level": 8,
        "base_damage": 6,
        "damage_per_level": 2,
        "speed": 0,
        "aggro_range": 230,
        "attack_range": 145,
        "ranged": True,
        "fragile": True,
        "color": (53, 145, 68),
        "xp": 16,
        "coins": 7,
        "drops": {"herb": (0.45, 1, 2), "basic_seed": (0.25, 1, 2)},
    },
    "water_sprite": {
        "name": "Espirito d'Agua",
        "biome": "agua",
        "base_hp": 20,
        "hp_per_level": 6,
        "base_damage": 7,
        "damage_per_level": 2,
        "speed": 86,
        "aggro_range": 260,
        "attack_range": 160,
        "ranged": True,
        "fragile": True,
        "color": (70, 154, 211),
        "xp": 18,
        "coins": 9,
        "drops": {"water_flask": (0.45, 1, 2), "small_fish": (0.18, 1, 1)},
    },
    "mud_crab": {
        "name": "Caranguejo de Lama",
        "biome": "agua",
        "base_hp": 38,
        "hp_per_level": 13,
        "base_damage": 6,
        "damage_per_level": 2,
        "speed": 58,
        "aggro_range": 175,
        "attack_range": 36,
        "ranged": False,
        "fragile": False,
        "color": (164, 105, 69),
        "xp": 17,
        "coins": 7,
        "drops": {"raw_meat": (0.42, 1, 1), "stone": (0.35, 1, 2)},
    },
    "ice_wisp": {
        "name": "Fagulha de Gelo",
        "biome": "gelo",
        "base_hp": 18,
        "hp_per_level": 6,
        "base_damage": 8,
        "damage_per_level": 3,
        "speed": 94,
        "aggro_range": 270,
        "attack_range": 175,
        "ranged": True,
        "fragile": True,
        "color": (147, 213, 234),
        "xp": 20,
        "coins": 10,
        "drops": {"simple_ore": (0.30, 1, 1), "water_flask": (0.25, 1, 1)},
    },
}


ENEMY_ORDER = [
    "forest_slime",
    "young_wolf",
    "forest_bat",
    "thorn_plant",
    "water_sprite",
    "mud_crab",
    "ice_wisp",
]


def _load_json_mobs() -> None:
    data = load_json(BASE_DIR / "src" / "data" / "mobs.json", {"mobs": []})
    for mob in data.get("mobs", []):
        mob_id = mob.get("id")
        if not mob_id or mob_id in ENEMY_TYPES:
            continue
        stats = mob.get("stats", {})
        drops = {
            drop["id"]: (float(drop.get("chance", 0)), int(drop.get("min", 1)), int(drop.get("max", 1)))
            for drop in mob.get("drops", [])
            if drop.get("id")
        }
        level = int(mob.get("level", 1))
        ENEMY_TYPES[mob_id] = {
            "name": mob.get("name", mob_id),
            "biome": ",".join(mob.get("biomes", [])),
            "base_hp": int(stats.get("health", 25)),
            "hp_per_level": max(5, int(stats.get("health", 25)) // 4),
            "base_damage": int(stats.get("damage", 5)),
            "damage_per_level": max(1, int(stats.get("damage", 5)) // 4),
            "speed": float(stats.get("speed", 70)),
            "aggro_range": int(stats.get("aggro_range", 230)),
            "attack_range": int(stats.get("attack_range", 150 if stats.get("ranged") else 34)),
            "ranged": bool(stats.get("ranged", False)),
            "fragile": mob.get("rarity") in {"common", "uncommon"} and int(stats.get("health", 25)) < 40,
            "color": tuple(stats.get("color", (94 + level * 18, 90 + level * 8, 88 + level * 12))),
            "xp": int(stats.get("xp_reward", 12)),
            "coins": int(stats.get("coins", level * 5)),
            "drops": drops,
            "spawn_phases": mob.get("spawn_phases", []),
            "biomes": mob.get("biomes", []),
            "max_per_chunk": int(mob.get("max_per_chunk", 2)),
            "spawn_level": level,
            "rarity": mob.get("rarity", "common"),
        }
        ENEMY_ORDER.append(mob_id)


_load_json_mobs()
