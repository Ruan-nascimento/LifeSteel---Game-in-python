from __future__ import annotations

import pygame

from src.core.settings import COLORS, Settings
from src.ui.widgets import draw_text


class NotificationUI:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    def push(self, text: str, color=None, duration: float = 3.2) -> None:
        self.messages.append({"text": text, "timer": duration, "duration": duration, "color": color or COLORS["white"]})
        self.messages = self.messages[-6:]

    def update(self, dt: float) -> None:
        for message in self.messages:
            message["timer"] -= dt
        self.messages = [message for message in self.messages if message["timer"] > 0]

    def draw(self, surface: pygame.Surface) -> None:
        y = 112
        for message in self.messages:
            alpha = max(0, min(255, int(255 * min(1, message["timer"] / 0.8))))
            text = str(message["text"])
            font = pygame.font.SysFont(Settings.UI_FONT, Settings.UI_SMALL_FONT_SIZE, bold=True)
            width = font.size(text)[0] + 24
            panel = pygame.Surface((width, 28), pygame.SRCALPHA)
            pygame.draw.rect(panel, (*COLORS["panel_dark"], min(210, alpha)), panel.get_rect(), border_radius=5)
            surface.blit(panel, (18, y))
            draw_text(surface, text, (30, y + 6), message.get("color", COLORS["white"]), Settings.UI_SMALL_FONT_SIZE, bold=True)
            y += 32
