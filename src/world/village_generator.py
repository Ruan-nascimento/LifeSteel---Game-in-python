from __future__ import annotations

import random
from dataclasses import dataclass

import pygame

from src.core.json_loader import load_json
from src.core.settings import BASE_DIR, Settings


LOCATIONS_PATH = BASE_DIR / "src" / "data" / "locations.json"


@dataclass
class Village:
    location_id: str
    name: str
    tile: tuple[int, int]
    safe_radius_tiles: int
    vendors: list[str]
    biome: str

    @property
    def rect(self) -> pygame.Rect:
        radius = self.safe_radius_tiles * Settings.TILE_SIZE
        center = pygame.Vector2((self.tile[0] + 0.5) * Settings.TILE_SIZE, (self.tile[1] + 0.5) * Settings.TILE_SIZE)
        return pygame.Rect(center.x - radius, center.y - radius, radius * 2, radius * 2)

    def to_dict(self) -> dict:
        return {
            "location_id": self.location_id,
            "name": self.name,
            "tile": list(self.tile),
            "safe_radius_tiles": self.safe_radius_tiles,
            "vendors": list(self.vendors),
            "biome": self.biome,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Village":
        return cls(
            location_id=str(data["location_id"]),
            name=str(data.get("name", data["location_id"])),
            tile=tuple(data["tile"]),
            safe_radius_tiles=int(data.get("safe_radius_tiles", 8)),
            vendors=list(data.get("vendors", [])),
            biome=str(data.get("biome", "village_region")),
        )


class VillageGenerator:
    def __init__(self, seed: int, locations_path=LOCATIONS_PATH) -> None:
        self.seed = seed
        data = load_json(locations_path, {"locations": []})
        self.location_defs = [entry for entry in data.get("locations", []) if entry.get("type") == "village"]

    def generate_villages(self, width: int, height: int, spawn_tile: tuple[int, int]) -> list[Village]:
        rng = random.Random(f"{self.seed}:villages")
        result: list[Village] = []
        preferred_offsets = [(44, -30), (-58, 38), (70, 55), (-76, -64)]
        for index, location in enumerate(self.location_defs[:4]):
            if index < len(preferred_offsets):
                ox, oy = preferred_offsets[index]
                tile = (spawn_tile[0] + ox, spawn_tile[1] + oy)
            else:
                tile = (rng.randint(24, width - 25), rng.randint(24, height - 25))
            tile = (max(12, min(width - 13, tile[0])), max(12, min(height - 13, tile[1])))
            result.append(
                Village(
                    location_id=location["id"],
                    name=location["name"],
                    tile=tile,
                    safe_radius_tiles=int(location.get("safe_radius_tiles", 9)),
                    vendors=list(location.get("vendors", [])),
                    biome=location.get("biome", "village_region"),
                )
            )
        return result

    def apply_to_tiles(self, tiles, villages: list[Village]) -> None:
        width = len(tiles[0])
        height = len(tiles)
        for village in villages:
            cx, cy = village.tile
            radius = village.safe_radius_tiles
            for y in range(cy - radius, cy + radius + 1):
                for x in range(cx - radius, cx + radius + 1):
                    if not (0 <= x < width and 0 <= y < height):
                        continue
                    dist = abs(x - cx) + abs(y - cy)
                    if dist <= radius:
                        tiles[y][x].kind = "grass_light"
                    if x == cx or y == cy or dist in {radius - 2, radius - 1}:
                        tiles[y][x].kind = "path"
