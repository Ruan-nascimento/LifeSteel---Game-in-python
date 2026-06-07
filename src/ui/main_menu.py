from __future__ import annotations

import math

import pygame

from src.core.settings import COLORS, Settings
from src.ui.widgets import Button, draw_text


class MainMenu:
    def __init__(self, save_manager) -> None:
        self.save_manager = save_manager
        self.buttons: list[Button] = []
        self.timer = 0.0

    def update(self, dt: float) -> None:
        self.timer += dt

    def handle_event(self, event) -> str | None:
        if event.type in {pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION}:
            for button in self.buttons:
                action = button.handle_event(event)
                if action:
                    return action
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((38, 82, 57))
        self._draw_forest(surface)
        draw_text(surface, "LifeSteel", (surface.get_width() // 2, 118), COLORS["accent"], 64, bold=True, center=True)
        draw_text(surface, "Sobreviva. Construa. Transforme a floresta em vila.", (surface.get_width() // 2, 182), COLORS["white"], 18, center=True)

        button_w = 260
        x = surface.get_width() // 2 - button_w // 2
        y = 250
        specs = [
            ("Novo Jogo", "new_game", False),
            ("Continuar", "continue", not self.save_manager.has_save()),
            ("Configuracoes", "settings", False),
            ("Sair", "quit", False),
        ]
        self.buttons = []
        for index, (label, action, disabled) in enumerate(specs):
            button = Button((x, y + index * 58, button_w, 42), label, action, disabled)
            button.draw(surface)
            self.buttons.append(button)

    def _draw_forest(self, surface: pygame.Surface) -> None:
        width, height = surface.get_size()
        for y in range(0, height, 32):
            color = (34 + y // 40, 76 + y // 28, 53)
            pygame.draw.rect(surface, color, (0, y, width, 32))
        for i in range(48):
            x = (i * 83 + int(self.timer * 18)) % (width + 80) - 40
            base_y = 260 + (i * 37) % (height - 260)
            sway = math.sin(self.timer + i) * 5
            trunk = pygame.Rect(x + sway, base_y + 28, 8, 34)
            pygame.draw.rect(surface, (88, 57, 33), trunk)
            pygame.draw.circle(surface, (30, 103, 50), (int(x + 4 + sway), base_y + 22), 24)
            pygame.draw.circle(surface, (48, 130, 61), (int(x - 10 + sway), base_y + 31), 16)
            pygame.draw.circle(surface, (40, 119, 54), (int(x + 18 + sway), base_y + 31), 16)
        for i in range(18):
            leaf_x = (i * 129 + self.timer * 38) % width
            leaf_y = (i * 53 + math.sin(self.timer + i) * 24) % height
            pygame.draw.circle(surface, (93, 157, 73), (int(leaf_x), int(leaf_y)), 3)
