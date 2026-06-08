from __future__ import annotations

import random
from dataclasses import dataclass, field

import pygame

from src.core.json_loader import load_json
from src.core.settings import BASE_DIR, Settings
from src.systems.inventory_system import InventorySlot
from src.world.resource_node import ResourceNode
from src.world.tile import Tile


CAVE_LOOT_PATH = BASE_DIR / "src" / "data" / "cave_loot_tables.json"


@dataclass
class CaveEntrance:
    cave_id: str
    tile: tuple[int, int]
    difficulty_level: int = 1

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.tile[0] * Settings.TILE_SIZE, self.tile[1] * Settings.TILE_SIZE, Settings.TILE_SIZE, Settings.TILE_SIZE)

    def interact(self, player) -> str:
        return self.cave_id

    def to_dict(self) -> dict:
        return {"cave_id": self.cave_id, "tile": list(self.tile), "difficulty_level": self.difficulty_level}

    @classmethod
    def from_dict(cls, data: dict) -> "CaveEntrance":
        return cls(str(data["cave_id"]), tuple(data["tile"]), int(data.get("difficulty_level", 1)))


@dataclass
class Cave:
    cave_id: str
    seed: int
    difficulty_level: int
    width: int = 64
    height: int = 64
    tiles: list[list[Tile]] = field(default_factory=list)
    resources: list[ResourceNode] = field(default_factory=list)
    structures: list = field(default_factory=list)
    drops: list = field(default_factory=list)
    spawn_tile: tuple[int, int] = (4, 4)
    exit_tile: tuple[int, int] = (4, 4)

    def to_dict(self, structure_state_serializer) -> dict:
        return {
            "cave_id": self.cave_id,
            "seed": self.seed,
            "difficulty_level": self.difficulty_level,
            "resources": [{"kind": r.kind, "tile_x": r.tile_x, "tile_y": r.tile_y, "hp": r.hp} for r in self.resources],
            "drops": [
                {
                    "item_id": d.item_id,
                    "quantity": d.quantity,
                    "pos": [d.pos.x, d.pos.y],
                    "contents": [slot.to_dict() if slot else None for slot in d.contents] if d.contents is not None else None,
                }
                for d in self.drops
            ],
            "structures": [
                {"building_id": s.building_id, "tile": list(s.tile), "state": structure_state_serializer(s)}
                for s in self.structures
            ],
        }


class CaveGenerator:
    def __init__(self, loot_path=CAVE_LOOT_PATH) -> None:
        self.loot_tables = load_json(loot_path, {"loot_tables": {}}).get("loot_tables", {})

    def generate_cave(self, cave_id: str, seed: int, difficulty_level: int):
        from src.world.world import Structure

        rng = random.Random(f"{seed}:{cave_id}:{difficulty_level}")
        cave = Cave(cave_id, seed, difficulty_level)
        cave.tiles = []
        for y in range(cave.height):
            row: list[Tile] = []
            for x in range(cave.width):
                edge = x in {0, cave.width - 1} or y in {0, cave.height - 1}
                kind = "grass_dark" if edge else ("water" if rng.random() < 0.035 else ("path" if rng.random() < 0.22 else "soil"))
                row.append(Tile(x, y, kind))
            cave.tiles.append(row)
        cave.spawn_tile = (4, cave.height // 2)
        cave.exit_tile = cave.spawn_tile
        for y in range(cave.spawn_tile[1] - 2, cave.spawn_tile[1] + 3):
            for x in range(cave.spawn_tile[0] - 2, cave.spawn_tile[0] + 3):
                cave.tiles[y][x].kind = "path"

        resource_amount = 45 + difficulty_level * 8
        for _ in range(resource_amount):
            x = rng.randint(6, cave.width - 5)
            y = rng.randint(5, cave.height - 5)
            if cave.tiles[y][x].kind == "water":
                continue
            kind = rng.choices(["stone", "ore", "bush"], weights=[45, 36 + difficulty_level * 4, 12], k=1)[0]
            cave.resources.append(ResourceNode(kind, x, y))

        chest_count = min(5, 2 + difficulty_level)
        for index in range(chest_count):
            for _ in range(80):
                x = rng.randint(8, cave.width - 7)
                y = rng.randint(7, cave.height - 7)
                if cave.tiles[y][x].kind != "water":
                    rarity = self._rarity_for_depth(rng, difficulty_level, index)
                    cave.structures.append(Structure("small_chest", (x, y), {"contents": self._roll_chest_contents(rng, rarity), "loot_rarity": rarity}))
                    break
        return cave

    def _rarity_for_depth(self, rng: random.Random, difficulty_level: int, index: int) -> str:
        roll = rng.random() + difficulty_level * 0.07 + index * 0.03
        if roll > 0.93:
            return "epic"
        if roll > 0.72:
            return "rare"
        if roll > 0.43:
            return "uncommon"
        return "common"

    def _roll_chest_contents(self, rng: random.Random, rarity: str) -> list[InventorySlot | None]:
        contents: list[InventorySlot | None] = [None for _ in range(12)]
        slot_index = 0
        for entry in self.loot_tables.get(rarity, []):
            if rng.random() > float(entry.get("chance", 1.0)):
                continue
            item_id = entry["id"]
            amount = rng.randint(int(entry.get("min", 1)), int(entry.get("max", 1)))
            if item_id == "coins":
                item_id = "zyra_coin_pouch"
            contents[slot_index] = InventorySlot(item_id, amount)
            slot_index += 1
            if slot_index >= len(contents):
                break
        return contents
