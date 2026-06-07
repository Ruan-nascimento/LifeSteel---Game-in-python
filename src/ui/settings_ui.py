from __future__ import annotations

import pygame

from src.core.settings import COLORS
from src.ui.widgets import Button, draw_panel, draw_text


class SettingsMenu:
    def __init__(self) -> None:
        self.volume_master = 80
        self.volume_music = 65
        self.volume_sfx = 80
        self.fullscreen = False
        self.show_fps = True
        self.language = "PT-BR"
        self.buttons: list[Button] = []

    def handle_event(self, event) -> str | None:
        if event.type in {pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION}:
            for button in self.buttons:
                action = button.handle_event(event)
                if action:
                    self._apply_action(action)
                    return action if action == "back" else None
        return None

    def _apply_action(self, action: str) -> None:
        if action == "master_minus":
            self.volume_master = max(0, self.volume_master - 5)
        elif action == "master_plus":
            self.volume_master = min(100, self.volume_master + 5)
        elif action == "music_minus":
            self.volume_music = max(0, self.volume_music - 5)
        elif action == "music_plus":
            self.volume_music = min(100, self.volume_music + 5)
        elif action == "sfx_minus":
            self.volume_sfx = max(0, self.volume_sfx - 5)
        elif action == "sfx_plus":
            self.volume_sfx = min(100, self.volume_sfx + 5)
        elif action == "fullscreen":
            self.fullscreen = not self.fullscreen
        elif action == "show_fps":
            self.show_fps = not self.show_fps

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((31, 56, 51))
        panel = pygame.Rect(surface.get_width() // 2 - 300, surface.get_height() // 2 - 245, 600, 490)
        draw_panel(surface, panel, "Configuracoes")
        self.buttons = []
        rows = [
            ("Volume geral", self.volume_master, "master_minus", "master_plus"),
            ("Volume musica", self.volume_music, "music_minus", "music_plus"),
            ("Volume efeitos", self.volume_sfx, "sfx_minus", "sfx_plus"),
        ]
        y = panel.y + 82
        for label, value, minus, plus in rows:
            draw_text(surface, label, (panel.x + 34, y + 7), COLORS["white"], 17)
            draw_text(surface, f"{value:3d}", (panel.x + 320, y + 7), COLORS["accent"], 17, bold=True)
            b1 = Button((panel.x + 380, y, 38, 32), "-", minus)
            b2 = Button((panel.x + 426, y, 38, 32), "+", plus)
            b1.draw(surface)
            b2.draw(surface)
            self.buttons.extend([b1, b2])
            y += 58

        toggles = [
            ("Tela cheia", self.fullscreen, "fullscreen"),
            ("Mostrar FPS", self.show_fps, "show_fps"),
        ]
        for label, value, action in toggles:
            draw_text(surface, label, (panel.x + 34, y + 7), COLORS["white"], 17)
            button = Button((panel.x + 380, y, 84, 32), "ON" if value else "OFF", action)
            button.draw(surface)
            self.buttons.append(button)
            y += 58

        draw_text(surface, "Resolucao: 1280x720 redimensionavel", (panel.x + 34, y + 4), COLORS["white"], 15)
        draw_text(surface, f"Idioma: {self.language}", (panel.x + 34, y + 34), COLORS["white"], 15)
        back = Button((panel.centerx - 70, panel.bottom - 62, 140, 40), "Voltar", "back")
        back.draw(surface)
        self.buttons.append(back)
