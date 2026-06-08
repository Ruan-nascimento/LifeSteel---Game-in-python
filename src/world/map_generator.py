from __future__ import annotations

import math
import random

from src.core.settings import Settings
from src.world.biome import BIOMES, biome_for_chunk
from src.world.resource_node import ResourceNode
from src.world.tile import Tile


class MapGenerator:
    def __init__(self, seed: int = 1337) -> None:
        self.random = random.Random(seed)
        self.seed = seed

    def generate(self) -> tuple[list[list[Tile]], list[ResourceNode], tuple[int, int], tuple[int, int]]:
        width = Settings.WORLD_WIDTH
        height = Settings.WORLD_HEIGHT
        tiles: list[list[Tile]] = []
        area_scale = max(1.0, (width * height) / (160 * 160))
        lakes = [
            (self.random.randint(15, width - 15), self.random.randint(15, height - 15), self.random.randint(5, 13))
            for _ in range(int(9 * area_scale))
        ]
        for y in range(height):
            row = []
            for x in range(width):
                biome_id = biome_for_chunk(self.seed, x // Settings.CHUNK_SIZE, y // Settings.CHUNK_SIZE)
                biome = BIOMES[biome_id]
                kind = self._weighted_tile_kind(biome.tile_weights)
                for lake_x, lake_y, radius in lakes:
                    distance = math.dist((x, y), (lake_x, lake_y))
                    if distance < radius:
                        kind = "water"
                    elif distance < radius + 1.5 and kind != "water":
                        kind = "soil"
                path_y = height // 2 + int(math.sin(x / 9) * 6)
                path_x = width // 2 + int(math.sin(y / 13) * 8)
                if (abs(y - path_y) <= 1 or abs(x - path_x) <= 1) and kind != "water":
                    kind = "path"
                row.append(Tile(x, y, kind))
            tiles.append(row)

        spawn_tile = (width // 2, height // 2)
        vendor_tile = (spawn_tile[0] + 18, spawn_tile[1] - 7)
        for y in range(spawn_tile[1] - 4, spawn_tile[1] + 5):
            for x in range(spawn_tile[0] - 4, spawn_tile[0] + 5):
                if 0 <= x < width and 0 <= y < height:
                    tiles[y][x].kind = "grass"
        for y in range(vendor_tile[1] - 3, vendor_tile[1] + 4):
            for x in range(vendor_tile[0] - 3, vendor_tile[0] + 4):
                if 0 <= x < width and 0 <= y < height:
                    tiles[y][x].kind = "path"

        resources = self._place_resources(tiles, spawn_tile, vendor_tile)
        return tiles, resources, spawn_tile, vendor_tile

    def _weighted_tile_kind(self, weights: dict[str, float]) -> str:
        total = sum(weights.values()) or 1.0
        roll = self.random.random() * total
        current = 0.0
        for kind, weight in weights.items():
            current += weight
            if roll <= current:
                return kind
        return next(iter(weights), "grass")

    def _place_resources(self, tiles, spawn_tile, vendor_tile) -> list[ResourceNode]:
        resources: list[ResourceNode] = []
        occupied = set()
        width = len(tiles[0])
        height = len(tiles)

        def can_place(x: int, y: int) -> bool:
            if not (0 <= x < width and 0 <= y < height):
                return False
            if tiles[y][x].kind in {"water", "path"}:
                return False
            if math.dist((x, y), spawn_tile) < 6 or math.dist((x, y), vendor_tile) < 5:
                return False
            return (x, y) not in occupied

        area_scale = max(1.0, (width * height) / (160 * 160))
        placements = [
            ("tree", int(640 * area_scale)),
            ("stone", int(230 * area_scale)),
            ("ore", int(80 * area_scale)),
            ("bush", int(210 * area_scale)),
            ("soil", int(90 * area_scale)),
        ]
        for kind, amount in placements:
            attempts = 0
            placed = 0
            while placed < amount and attempts < amount * 15:
                attempts += 1
                x = self.random.randint(3, width - 4)
                y = self.random.randint(3, height - 4)
                if can_place(x, y):
                    resources.append(ResourceNode(kind, x, y))
                    occupied.add((x, y))
                    placed += 1
        return resources
