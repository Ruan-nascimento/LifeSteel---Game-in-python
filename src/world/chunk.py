from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from src.core.settings import Settings


@dataclass
class Chunk:
    chunk_x: int
    chunk_y: int
    biome: str = "forest"
    modified: bool = False
    resources: list = field(default_factory=list)
    structures: list = field(default_factory=list)
    drops: list = field(default_factory=list)
    mobs: list = field(default_factory=list)
    cave_entrances: list = field(default_factory=list)
    villages: list = field(default_factory=list)
    npcs: list = field(default_factory=list)
    explored_tiles: set[tuple[int, int]] = field(default_factory=set)

    @property
    def tile_rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.chunk_x * Settings.CHUNK_SIZE,
            self.chunk_y * Settings.CHUNK_SIZE,
            Settings.CHUNK_SIZE,
            Settings.CHUNK_SIZE,
        )

    @property
    def world_rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.chunk_x * Settings.CHUNK_SIZE * Settings.TILE_SIZE,
            self.chunk_y * Settings.CHUNK_SIZE * Settings.TILE_SIZE,
            Settings.CHUNK_SIZE * Settings.TILE_SIZE,
            Settings.CHUNK_SIZE * Settings.TILE_SIZE,
        )

    def generate(self, seed: int) -> None:
        self.modified = False

    def update(self, dt: float) -> None:
        for drop in self.drops:
            drop.age += dt

    def render(self, screen, camera) -> None:
        return None

    def serialize(self) -> dict:
        return {
            "chunk_x": self.chunk_x,
            "chunk_y": self.chunk_y,
            "biome": self.biome,
            "modified": self.modified,
            "explored_tiles": [[x, y] for x, y in sorted(self.explored_tiles)],
        }

    def deserialize(self, data: dict) -> None:
        self.biome = data.get("biome", self.biome)
        self.modified = bool(data.get("modified", self.modified))
        self.explored_tiles = {(int(x), int(y)) for x, y in data.get("explored_tiles", [])}
