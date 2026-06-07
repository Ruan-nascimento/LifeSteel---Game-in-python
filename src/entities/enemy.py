from __future__ import annotations

import random

import pygame

from src.core.settings import COLORS, Settings
from src.data.enemies_data import ENEMY_TYPES
from src.entities.entity import Entity


class Enemy(Entity):
    def __init__(self, kind: str, pos, asset_loader, base_level: int = 1) -> None:
        self.data = ENEMY_TYPES[kind]
        self.base_level = max(1, min(5, int(base_level)))
        self.level = self.base_level
        hp = self._scaled_hp(self.level)
        super().__init__(pos, size=(34, 30), hp=hp)
        self.name = self.data["name"]
        self.kind = kind
        self.assets = asset_loader
        self.speed = float(self.data["speed"])
        self.damage = self._scaled_damage(self.level)
        self.attack_cooldown = 0.0
        self.aggro_range = int(self.data["aggro_range"])
        self.attack_range = int(self.data["attack_range"])
        self.ranged = bool(self.data["ranged"])

    def _scaled_hp(self, level: int) -> int:
        return int(self.data["base_hp"] + self.data["hp_per_level"] * (level - 1))

    def _scaled_damage(self, level: int) -> int:
        return int(self.data["base_damage"] + self.data["damage_per_level"] * (level - 1))

    def sync_level_with_player(self, player_level: int) -> None:
        new_level = self.base_level + max(0, player_level // 5)
        if new_level == self.level:
            return
        ratio = self.hp / self.max_hp if self.max_hp > 0 else 1
        self.level = new_level
        self.max_hp = self._scaled_hp(self.level)
        self.hp = max(1, self.max_hp * ratio)
        self.damage = self._scaled_damage(self.level)

    def update(self, dt: float, player, world) -> None:
        self.sync_level_with_player(player.level.level)
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        if not self.alive:
            return
        distance = self.center.distance_to(player.center)
        if distance < self.aggro_range and self.speed > 0:
            direction = player.center - self.center
            if direction.length_squared() > 0:
                direction = direction.normalize()
                if self.ranged and distance < self.attack_range * 0.45:
                    direction *= -1
                elif self.ranged and distance <= self.attack_range * 0.85:
                    return
                elif not self.ranged and distance <= 28:
                    return
                delta = direction * self.speed * dt
                self._move_axis(delta.x, 0, world)
                self._move_axis(0, delta.y, world)

    def _move_axis(self, dx: float, dy: float, world) -> None:
        self.pos.x += dx
        if world.collides(self.collision_rect):
            self.pos.x -= dx
        self.pos.y += dy
        if world.collides(self.collision_rect):
            self.pos.y -= dy

    def draw(self, surface: pygame.Surface, camera) -> None:
        if not self.alive:
            return
        image = self.assets.enemies[self.kind]
        surface.blit(image, self.pos - camera.offset - pygame.Vector2(image.get_width() / 2, image.get_height() / 2))
        self._draw_label(surface, camera)
        self.draw_health_bar(surface, camera)

    def _draw_label(self, surface: pygame.Surface, camera) -> None:
        rect = camera.apply(self.rect)
        label = f"{self.name} Lv {self.level}"
        font = pygame.font.SysFont(Settings.UI_FONT, 11, bold=True)
        image = font.render(label, True, COLORS["white"])
        shadow = font.render(label, True, COLORS["black"])
        label_rect = image.get_rect(center=(rect.centerx, rect.y - 18))
        surface.blit(shadow, label_rect.move(1, 1))
        surface.blit(image, label_rect)

    def reward_xp(self) -> int:
        return int(self.data["xp"] + self.level * 10)

    def reward_coins(self) -> int:
        return int(self.data["coins"] + self.level * 2)

    def drop_items(self) -> dict[str, int]:
        drops: dict[str, int] = {}
        for item_id, (chance, minimum, maximum) in self.data.get("drops", {}).items():
            if random.random() <= chance:
                drops[item_id] = drops.get(item_id, 0) + random.randint(minimum, maximum)
        return drops
