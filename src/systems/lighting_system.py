from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from src.core.settings import Settings


@dataclass(frozen=True)
class LightSource:
    pos: pygame.Vector2
    radius: int
    intensity: float = 1.0


class LightingSystem:
    def __init__(self, screen_size: tuple[int, int]) -> None:
        self.screen_size = screen_size
        self.darkness = pygame.Surface(screen_size, pygame.SRCALPHA)
        self._mask_cache: dict[tuple[int, int], pygame.Surface] = {}
        self._frame = 0
        self.processed_lights = 0

    def resize(self, screen_size: tuple[int, int]) -> None:
        if screen_size == self.screen_size:
            return
        self.screen_size = screen_size
        self.darkness = pygame.Surface(screen_size, pygame.SRCALPHA)

    def get_light_mask(self, radius: int, intensity: float = 1.0) -> pygame.Surface:
        radius = max(1, int(radius))
        intensity_key = max(5, min(100, int(intensity * 100)))
        cache_key = (radius, intensity_key)
        cached = self._mask_cache.get(cache_key)
        if cached:
            return cached

        diameter = radius * 2
        mask = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        center = (radius, radius)
        max_subtract = int(255 * (intensity_key / 100))
        for step in range(radius, 0, -4):
            distance_ratio = step / radius
            alpha = int(max_subtract * (distance_ratio ** 1.65))
            pygame.draw.circle(mask, (0, 0, 0, alpha), center, step)
        self._mask_cache[cache_key] = mask
        return mask

    def render(self, surface: pygame.Surface, camera, time_system, light_sources, player=None, weather_system=None) -> int:
        alpha = int(time_system.get_darkness_alpha())
        if weather_system and getattr(weather_system, "current", "") == "Nevoeiro":
            alpha = min(230, alpha + 24)
        if alpha <= 0:
            self.processed_lights = 0
            return 0

        self.resize(surface.get_size())
        self.darkness.fill((0, 0, 0, alpha))
        self._frame += 1

        screen_rect = pygame.Rect(-Settings.RENDER_MARGIN, -Settings.RENDER_MARGIN, surface.get_width() + Settings.RENDER_MARGIN * 2, surface.get_height() + Settings.RENDER_MARGIN * 2)
        lights: list[LightSource] = []
        if player:
            radius = 82
            if hasattr(player, "count_item") and player.count_item("anel_da_primeira_noite") > 0:
                radius += 18
            lights.append(LightSource(pygame.Vector2(player.center), radius, 0.92))
        for raw in light_sources or []:
            if isinstance(raw, LightSource):
                lights.append(raw)
            else:
                pos, radius, *_ = raw
                lights.append(LightSource(pygame.Vector2(pos), int(radius), 1.0))

        processed = 0
        for light in lights:
            screen_pos = light.pos - camera.offset
            if not screen_rect.collidepoint(int(screen_pos.x), int(screen_pos.y)):
                continue
            radius = light.radius
            if Settings.ENABLE_LIGHT_FLICKER and light.radius > 85:
                radius += int(math.sin((self._frame + light.pos.x * 0.01) * 0.11) * 4)
            mask = self.get_light_mask(radius, light.intensity)
            self.darkness.blit(mask, (screen_pos.x - radius, screen_pos.y - radius), special_flags=pygame.BLEND_RGBA_SUB)
            processed += 1

        surface.blit(self.darkness, (0, 0))
        self.processed_lights = processed
        return processed
