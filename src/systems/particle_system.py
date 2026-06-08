from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

from src.core.settings import Settings


@dataclass
class Particle:
    pos: pygame.Vector2
    velocity: pygame.Vector2
    color: tuple[int, int, int]
    lifetime: float
    radius: float
    max_lifetime: float

    def update(self, dt: float) -> bool:
        self.pos += self.velocity * dt
        self.velocity *= 0.94
        self.lifetime -= dt
        return self.lifetime > 0

    def draw(self, surface: pygame.Surface, camera, visible_rect: pygame.Rect | None = None) -> bool:
        if self.lifetime <= 0:
            return False
        if visible_rect and not visible_rect.collidepoint(int(self.pos.x), int(self.pos.y)):
            return False
        alpha = max(0, min(255, int(255 * (self.lifetime / self.max_lifetime))))
        radius = max(1, int(self.radius * (self.lifetime / self.max_lifetime)))
        color = tuple(max(0, min(255, int(channel * (alpha / 255)))) for channel in self.color)
        pygame.draw.circle(surface, color, self.pos - camera.offset, radius)
        return True


class ParticleManager:
    def __init__(self) -> None:
        self.particles: list[Particle] = []

    def emit(self, pos, color=(255, 255, 255), amount: int = 8, speed: float = 80, lifetime: float = 0.6, radius: float = 3) -> None:
        if Settings.LOW_PERFORMANCE_MODE:
            amount = max(1, amount // 2)
        free_slots = max(0, Settings.MAX_PARTICLES - len(self.particles))
        amount = min(amount, free_slots)
        if amount <= 0:
            return
        origin = pygame.Vector2(pos)
        for _ in range(amount):
            angle = random.uniform(0, math.tau)
            magnitude = random.uniform(speed * 0.25, speed)
            velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * magnitude
            self.particles.append(
                Particle(
                    pos=origin.copy(),
                    velocity=velocity,
                    color=color,
                    lifetime=random.uniform(lifetime * 0.65, lifetime * 1.25),
                    radius=random.uniform(max(1, radius - 1), radius + 1.5),
                    max_lifetime=lifetime,
                )
            )

    def trail(self, pos, color=(160, 138, 98)) -> None:
        self.emit(pos, color=color, amount=2, speed=25, lifetime=0.28, radius=2)

    def update(self, dt: float) -> None:
        self.particles = [particle for particle in self.particles if particle.update(dt)]
        if len(self.particles) > Settings.MAX_PARTICLES:
            self.particles = self.particles[-Settings.MAX_PARTICLES:]

    def draw(self, surface: pygame.Surface, camera) -> int:
        visible_rect = pygame.Rect(
            camera.offset.x - Settings.RENDER_MARGIN,
            camera.offset.y - Settings.RENDER_MARGIN,
            camera.screen_width + Settings.RENDER_MARGIN * 2,
            camera.screen_height + Settings.RENDER_MARGIN * 2,
        )
        drawn = 0
        for particle in self.particles:
            if particle.draw(surface, camera, visible_rect):
                drawn += 1
        return drawn
