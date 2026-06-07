from __future__ import annotations

import pygame

from src.core.settings import COLORS
from src.ui.widgets import draw_panel, draw_text, draw_wrapped


class DialogueUI:
    def __init__(self) -> None:
        self.npc = None
        self.line_index = 0

    def open(self, npc) -> None:
        self.npc = npc
        self.line_index = 0

    def close(self) -> None:
        self.npc = None

    def handle_event(self, event) -> str | None:
        if not self.npc:
            return None
        if event.type == pygame.KEYDOWN and event.key in {pygame.K_SPACE, pygame.K_RETURN, pygame.K_e}:
            self.line_index += 1
            if self.line_index >= len(self.npc.dialogue):
                return "close_dialogue"
        return None

    def draw(self, surface: pygame.Surface) -> None:
        if not self.npc:
            return
        panel = pygame.Rect(90, surface.get_height() - 176, surface.get_width() - 180, 132)
        draw_panel(surface, panel, f"{self.npc.name} - {self.npc.profession}")
        line = self.npc.dialogue[min(self.line_index, len(self.npc.dialogue) - 1)]
        draw_wrapped(surface, line, pygame.Rect(panel.x + 22, panel.y + 52, panel.width - 44, 48), COLORS["white"], 17)
        draw_text(surface, "Espaco/E para continuar", (panel.right - 210, panel.bottom - 28), (172, 181, 170), 13)
