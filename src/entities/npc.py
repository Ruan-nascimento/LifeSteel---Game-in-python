from __future__ import annotations

import math

import pygame

from src.entities.entity import Entity


class NPC(Entity):
    def __init__(self, name: str, profession: str, pos, asset_loader, vendor: bool = False, vendor_id: str | None = None, location_id: str | None = None, dialogue: list[str] | None = None) -> None:
        super().__init__(pos, size=(28, 40), hp=80)
        self.name = name
        self.profession = profession
        self.assets = asset_loader
        self.vendor = vendor
        self.vendor_id = vendor_id or ("vendor_milo_root" if vendor else None)
        self.location_id = location_id
        self.friendship = 0
        self.romance = 0
        self.dialogue = dialogue or [
            "A floresta parece calma hoje.",
            "A loja abre enquanto houver luz suficiente.",
            "Comunicacao alta sempre melhora bons acordos.",
        ]
        self._routine_time = 0.0
        self._origin = pygame.Vector2(pos)

    def update(self, dt: float) -> None:
        self._routine_time += dt
        offset = pygame.Vector2(math.sin(self._routine_time * 0.4) * 10, math.cos(self._routine_time * 0.25) * 6)
        self.pos = self._origin + offset

    def can_open_shop(self, player, time_system) -> bool:
        return self.vendor and self.center.distance_to(player.center) < 72 and time_system.shop_is_open()

    def draw(self, surface: pygame.Surface, camera) -> None:
        image = self.assets.npcs["vendor"]
        surface.blit(image, self.pos - camera.offset - pygame.Vector2(image.get_width() / 2, image.get_height() - 2))
