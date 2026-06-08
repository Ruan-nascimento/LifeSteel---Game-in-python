from __future__ import annotations

import math

import pygame

from src.core.settings import Settings
from src.world.biome import biome_for_chunk
from src.world.chunk import Chunk


class ChunkManager:
    def __init__(self, world, seed: int) -> None:
        self.world = world
        self.seed = seed
        self.chunks: dict[tuple[int, int], Chunk] = {}
        self.active_chunks: set[tuple[int, int]] = set()
        self.visible_chunks: set[tuple[int, int]] = set()

    @property
    def chunks_wide(self) -> int:
        return math.ceil(self.world.width / Settings.CHUNK_SIZE)

    @property
    def chunks_high(self) -> int:
        return math.ceil(self.world.height / Settings.CHUNK_SIZE)

    def get_chunk_coords_from_world_pos(self, world_x, world_y) -> tuple[int, int]:
        return (
            int(world_x // (Settings.CHUNK_SIZE * Settings.TILE_SIZE)),
            int(world_y // (Settings.CHUNK_SIZE * Settings.TILE_SIZE)),
        )

    def get_chunk_coords_from_tile(self, tile_x: int, tile_y: int) -> tuple[int, int]:
        return (int(tile_x // Settings.CHUNK_SIZE), int(tile_y // Settings.CHUNK_SIZE))

    def in_bounds(self, chunk_x: int, chunk_y: int) -> bool:
        return 0 <= chunk_x < self.chunks_wide and 0 <= chunk_y < self.chunks_high

    def get_chunk(self, chunk_x: int, chunk_y: int) -> Chunk | None:
        if not self.in_bounds(chunk_x, chunk_y):
            return None
        return self.load_chunk(chunk_x, chunk_y)

    def load_chunk(self, chunk_x: int, chunk_y: int) -> Chunk:
        key = (chunk_x, chunk_y)
        chunk = self.chunks.get(key)
        if chunk is None:
            chunk = Chunk(chunk_x, chunk_y, biome_for_chunk(self.seed, chunk_x, chunk_y))
            chunk.generate(self.seed)
            self.chunks[key] = chunk
        self.refresh_chunk_contents(chunk)
        return chunk

    def refresh_chunk_contents(self, chunk: Chunk) -> None:
        tile_rect = chunk.tile_rect
        chunk.resources = [res for res in getattr(self.world, "resources", []) if tile_rect.collidepoint(res.tile_x, res.tile_y)]
        chunk.structures = [struct for struct in getattr(self.world, "structures", []) if tile_rect.collidepoint(*struct.tile)]
        chunk.drops = [drop for drop in getattr(self.world, "drops", []) if tile_rect.collidepoint(*self.world.pixel_to_tile(drop.pos))]
        chunk.cave_entrances = [entrance for entrance in getattr(self.world, "cave_entrances", []) if tile_rect.collidepoint(*entrance.tile)]
        chunk.villages = [village for village in getattr(self.world, "villages", []) if tile_rect.collidepoint(*village.tile)]

    def unload_chunk(self, chunk_x: int, chunk_y: int) -> None:
        key = (chunk_x, chunk_y)
        chunk = self.chunks.get(key)
        if not chunk or chunk.modified or not Settings.UNLOAD_DISTANT_CHUNKS:
            return
        self.chunks.pop(key, None)

    def get_nearby_chunks(self, center_chunk_x: int, center_chunk_y: int, radius: int) -> list[Chunk]:
        chunks: list[Chunk] = []
        for cy in range(center_chunk_y - radius, center_chunk_y + radius + 1):
            for cx in range(center_chunk_x - radius, center_chunk_x + radius + 1):
                if self.in_bounds(cx, cy):
                    chunks.append(self.load_chunk(cx, cy))
        return chunks

    def update_active_chunks(self, player_pos) -> set[tuple[int, int]]:
        center_x, center_y = self.get_chunk_coords_from_world_pos(player_pos.x, player_pos.y)
        active = {
            (chunk.chunk_x, chunk.chunk_y)
            for chunk in self.get_nearby_chunks(center_x, center_y, Settings.ACTIVE_CHUNK_RADIUS)
        }
        self.active_chunks = active
        if Settings.UNLOAD_DISTANT_CHUNKS:
            for key in list(self.chunks):
                if key not in active and key not in self.visible_chunks:
                    self.unload_chunk(*key)
        return active

    def get_visible_chunks(self, camera) -> list[Chunk]:
        tile_size = Settings.TILE_SIZE
        chunk_tiles = Settings.CHUNK_SIZE
        start_cx = max(0, int(camera.offset.x // tile_size // chunk_tiles) - 1)
        end_cx = min(self.chunks_wide - 1, int((camera.offset.x + camera.screen_width) // tile_size // chunk_tiles) + 1)
        start_cy = max(0, int(camera.offset.y // tile_size // chunk_tiles) - 1)
        end_cy = min(self.chunks_high - 1, int((camera.offset.y + camera.screen_height) // tile_size // chunk_tiles) + 1)
        chunks = [self.load_chunk(cx, cy) for cy in range(start_cy, end_cy + 1) for cx in range(start_cx, end_cx + 1)]
        self.visible_chunks = {(chunk.chunk_x, chunk.chunk_y) for chunk in chunks}
        return chunks

    def tile_bounds_for_camera(self, camera) -> tuple[int, int, int, int]:
        chunks = self.get_visible_chunks(camera)
        if not chunks:
            return (0, 0, 0, 0)
        start_x = max(0, min(chunk.chunk_x for chunk in chunks) * Settings.CHUNK_SIZE)
        end_x = min(self.world.width, (max(chunk.chunk_x for chunk in chunks) + 1) * Settings.CHUNK_SIZE)
        start_y = max(0, min(chunk.chunk_y for chunk in chunks) * Settings.CHUNK_SIZE)
        end_y = min(self.world.height, (max(chunk.chunk_y for chunk in chunks) + 1) * Settings.CHUNK_SIZE)
        return start_x, end_x, start_y, end_y

    def is_active_tile(self, tile_x: int, tile_y: int) -> bool:
        return self.get_chunk_coords_from_tile(tile_x, tile_y) in self.active_chunks

    def chunk_key_for_rect(self, rect: pygame.Rect) -> tuple[int, int]:
        return self.get_chunk_coords_from_world_pos(rect.centerx, rect.centery)

    def mark_modified_at_tile(self, tile_x: int, tile_y: int) -> None:
        chunk = self.get_chunk(*self.get_chunk_coords_from_tile(tile_x, tile_y))
        if chunk:
            chunk.modified = True

    def serialize_modified_chunks(self) -> dict:
        return {
            f"{cx},{cy}": chunk.serialize()
            for (cx, cy), chunk in self.chunks.items()
            if chunk.modified
        }

    def deserialize_modified_chunks(self, data: dict) -> None:
        for key, raw in data.items():
            try:
                cx, cy = [int(part) for part in key.split(",", 1)]
            except ValueError:
                continue
            if not self.in_bounds(cx, cy):
                continue
            chunk = self.load_chunk(cx, cy)
            chunk.deserialize(raw)

    def render_visible_chunks(self, screen, camera) -> None:
        for chunk in self.get_visible_chunks(camera):
            chunk.render(screen, camera)
