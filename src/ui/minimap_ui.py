from __future__ import annotations

import pygame

from src.core.settings import COLORS, Settings
from src.ui.widgets import draw_text


class MinimapUI:
    TILE_COLORS = {
        "grass": (64, 134, 70),
        "grass_dark": (43, 103, 59),
        "grass_light": (92, 156, 78),
        "soil": (119, 84, 53),
        "path": (139, 119, 78),
        "water": (56, 128, 176),
    }

    RESOURCE_COLORS = {
        "tree": (31, 110, 48),
        "stone": (150, 154, 153),
        "ore": (204, 121, 63),
        "bush": (77, 167, 72),
        "soil": (145, 95, 56),
    }

    def __init__(self) -> None:
        self._cache_surface: pygame.Surface | None = None
        self._cache_key = None
        self._cache_time = 0

    def draw(self, surface: pygame.Surface, world, exploration, player, npcs=None, enemies=None, rect: pygame.Rect | None = None, expanded: bool = False) -> None:
        rect = rect or pygame.Rect(surface.get_width() - 205, surface.get_height() - 205, 185, 185)
        pygame.draw.rect(surface, COLORS["panel_dark"], rect, border_radius=6)
        pygame.draw.rect(surface, (87, 99, 88), rect, 2, border_radius=6)
        inner = rect.inflate(-12, -22)
        inner.y += 10
        cell_w = inner.width / world.width
        cell_h = inner.height / world.height
        now = pygame.time.get_ticks()
        explored_count = len(exploration.explored)
        cache_key = (world.seed, world.width, world.height, inner.size, expanded, explored_count, getattr(world, "current_cave_id", None))
        if expanded or self._cache_surface is None or self._cache_key != cache_key or now - self._cache_time > int(Settings.MINIMAP_UPDATE_INTERVAL * 1000):
            self._cache_surface = pygame.Surface(inner.size, pygame.SRCALPHA)
            step = 2 if expanded else 4
            for ty in range(0, world.height, step):
                for tx in range(0, world.width, step):
                    if not exploration.is_explored(tx, ty):
                        continue
                    tile = world.tiles[ty][tx]
                    color = self.TILE_COLORS.get(tile.kind, COLORS["grass"])
                    draw_rect = pygame.Rect(
                        int(tx * cell_w),
                        int(ty * cell_h),
                        max(1, int(cell_w * step) + 1),
                        max(1, int(cell_h * step) + 1),
                    )
                    self._cache_surface.fill(color, draw_rect)
            self._cache_key = cache_key
            self._cache_time = now
        if self._cache_surface:
            surface.blit(self._cache_surface, inner.topleft)

        if expanded:
            for resource in world.resources[:: max(1, len(world.resources) // 800)]:
                if exploration.is_explored(resource.tile_x, resource.tile_y):
                    pygame.draw.circle(
                        surface,
                        self.RESOURCE_COLORS.get(resource.kind, COLORS["white"]),
                        (inner.x + int(resource.tile_x * cell_w), inner.y + int(resource.tile_y * cell_h)),
                        2,
                    )

        for structure in world.structures:
            tx, ty = structure.tile
            if exploration.is_explored(tx, ty):
                pygame.draw.rect(surface, COLORS["accent"], (inner.x + int(tx * cell_w), inner.y + int(ty * cell_h), 3, 3))

        if expanded:
            for village in getattr(world, "villages", []):
                tx, ty = village.tile
                if exploration.is_explored(tx, ty):
                    pygame.draw.rect(surface, (240, 222, 96), (inner.x + int(tx * cell_w) - 2, inner.y + int(ty * cell_h) - 2, 5, 5))
            for entrance in getattr(world, "cave_entrances", []):
                tx, ty = entrance.tile
                if exploration.is_explored(tx, ty):
                    pygame.draw.circle(surface, (38, 32, 40), (inner.x + int(tx * cell_w), inner.y + int(ty * cell_h)), 3)

        if npcs:
            for npc in npcs:
                tx, ty = world.pixel_to_tile(npc.center)
                if exploration.is_explored(tx, ty):
                    pygame.draw.circle(surface, (240, 222, 96), (inner.x + int(tx * cell_w), inner.y + int(ty * cell_h)), 3)

        if enemies and expanded:
            for enemy in enemies:
                if enemy.alive:
                    tx, ty = world.pixel_to_tile(enemy.center)
                    if exploration.is_explored(tx, ty):
                        pygame.draw.circle(surface, COLORS["danger"], (inner.x + int(tx * cell_w), inner.y + int(ty * cell_h)), 2)

        ptx, pty = world.pixel_to_tile(player.center)
        pygame.draw.circle(surface, COLORS["white"], (inner.x + int(ptx * cell_w), inner.y + int(pty * cell_h)), 4 if expanded else 3)
        draw_text(surface, "Mapa", (rect.x + 10, rect.y + 4), COLORS["accent"], 14, bold=True)
