from __future__ import annotations

import pygame


class Camera:
    def __init__(self, screen_size: tuple[int, int], world_size: tuple[int, int]) -> None:
        self.screen_width, self.screen_height = screen_size
        self.world_width, self.world_height = world_size
        self.offset = pygame.Vector2(0, 0)

    def update(self, target_pos: pygame.Vector2) -> None:
        desired_x = target_pos.x - self.screen_width / 2
        desired_y = target_pos.y - self.screen_height / 2
        self.offset.x += (desired_x - self.offset.x) * 0.16
        self.offset.y += (desired_y - self.offset.y) * 0.16
        self.offset.x = max(0, min(self.offset.x, max(0, self.world_width - self.screen_width)))
        self.offset.y = max(0, min(self.offset.y, max(0, self.world_height - self.screen_height)))

    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        return rect.move(-int(self.offset.x), -int(self.offset.y))

    def world_to_screen(self, pos) -> pygame.Vector2:
        return pygame.Vector2(pos) - self.offset

    def screen_to_world(self, pos) -> pygame.Vector2:
        return pygame.Vector2(pos) + self.offset

    def resize(self, screen_size: tuple[int, int]) -> None:
        self.screen_width, self.screen_height = screen_size
