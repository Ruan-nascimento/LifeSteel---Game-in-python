from __future__ import annotations

import pygame


class Entity:
    def __init__(self, pos, size=(28, 36), hp: int = 100) -> None:
        self.pos = pygame.Vector2(pos)
        self.size = size
        self.max_hp = hp
        self.hp = hp
        self.alive = True
        self.direction = "down"
        self.facing_vector = pygame.Vector2(0, 1)
        self.image: pygame.Surface | None = None

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.pos.x - self.size[0] / 2),
            int(self.pos.y - self.size[1] / 2),
            self.size[0],
            self.size[1],
        )

    @property
    def collision_rect(self) -> pygame.Rect:
        rect = self.rect.copy()
        rect.height = int(rect.height * 0.45)
        rect.top = self.rect.bottom - rect.height
        rect.inflate_ip(-6, -2)
        return rect

    @property
    def center(self) -> pygame.Vector2:
        return pygame.Vector2(self.rect.center)

    def take_damage(self, amount: int) -> None:
        self.hp -= max(1, int(amount))
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def heal(self, amount: float) -> None:
        self.hp = min(self.max_hp, self.hp + max(0, amount))

    def draw_health_bar(self, surface: pygame.Surface, camera) -> None:
        if self.hp >= self.max_hp:
            return
        rect = camera.apply(self.rect)
        bg = pygame.Rect(rect.x, rect.y - 8, rect.width, 5)
        pygame.draw.rect(surface, (48, 20, 20), bg)
        fill = bg.copy()
        fill.width = max(1, int(bg.width * (self.hp / self.max_hp)))
        pygame.draw.rect(surface, (216, 68, 68), fill)
