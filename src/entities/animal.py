from __future__ import annotations

import random
import math

import pygame

from src.core.settings import COLORS, Settings
from src.data.animals_data import ANIMAL_TYPES
from src.entities.entity import Entity


class Animal(Entity):
    def __init__(self, kind: str, pos, asset_loader) -> None:
        self.kind = kind
        self.data = ANIMAL_TYPES[kind]
        super().__init__(pos, size=(32, 24), hp=int(self.data["hp"]))
        self.name = self.data["name"]
        self.assets = asset_loader
        self._origin = pygame.Vector2(pos)
        self._timer = 0.0
        self._wander_dir = pygame.Vector2(1, 0)
        self._wander_change = 0.0

    def update(self, dt: float, world=None) -> None:
        if not self.alive:
            return
        self._timer += dt
        self._wander_change -= dt
        if self._wander_change <= 0:
            angle = random.uniform(0, math.tau)
            self._wander_dir = pygame.Vector2(math.cos(angle), math.sin(angle))
            self._wander_change = random.uniform(1.2, 3.0)
        speed = float(self.data["speed"])
        delta = self._wander_dir * speed * dt
        if world:
            self._move_axis(delta.x, 0, world)
            self._move_axis(0, delta.y, world)
        else:
            self.pos += delta
        if self.pos.distance_to(self._origin) > 160:
            self._wander_dir = (self._origin - self.pos).normalize()

    def _move_axis(self, dx: float, dy: float, world) -> None:
        self.pos.x += dx
        if world.collides(self.collision_rect):
            self.pos.x -= dx
            self._wander_change = 0
        self.pos.y += dy
        if world.collides(self.collision_rect):
            self.pos.y -= dy
            self._wander_change = 0

    def draw(self, surface: pygame.Surface, camera) -> None:
        if not self.alive:
            return
        image = self.assets.animals[self.kind]
        surface.blit(image, self.pos - camera.offset - pygame.Vector2(image.get_width() / 2, image.get_height() / 2))
        self.draw_health_bar(surface, camera)

    def drop_items(self) -> dict[str, int]:
        drops: dict[str, int] = {}
        for item_id, (chance, minimum, maximum) in self.data.get("drops", {}).items():
            if random.random() <= chance:
                drops[item_id] = drops.get(item_id, 0) + random.randint(minimum, maximum)
        return drops
