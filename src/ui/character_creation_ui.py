from __future__ import annotations

import pygame

from src.core.settings import COLORS, Settings
from src.data.classes_data import CLASSES, CLASS_ORDER
from src.ui.widgets import Button, draw_panel, draw_text, draw_wrapped


class CharacterCreationMenu:
    def __init__(self, asset_loader) -> None:
        self.assets = asset_loader
        self.name = "Viajante"
        self.selected_class = "warrior"
        self.name_active = False
        self.buttons: list[Button] = []
        self.class_buttons: list[Button] = []

    def handle_event(self, event) -> tuple | str | None:
        if event.type == pygame.KEYDOWN and self.name_active:
            if event.key == pygame.K_BACKSPACE:
                self.name = self.name[:-1]
            elif event.key == pygame.K_RETURN:
                self.name_active = False
            elif len(self.name) < 18 and event.unicode and event.unicode.isprintable():
                self.name += event.unicode
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.name_rect.collidepoint(event.pos):
                self.name_active = True
                return None
            self.name_active = False
            for button in self.class_buttons + self.buttons:
                action = button.handle_event(event)
                if action:
                    if isinstance(action, tuple) and action[0] == "class":
                        self.selected_class = action[1]
                        return None
                    if action == "start":
                        return ("start_game", self.name.strip() or "Viajante", self.selected_class)
                    return action
        if event.type == pygame.MOUSEMOTION:
            for button in self.class_buttons + self.buttons:
                button.handle_event(event)
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((35, 70, 58))
        panel = pygame.Rect(surface.get_width() // 2 - 520, surface.get_height() // 2 - 305, 1040, 610)
        draw_panel(surface, panel, "Criacao de Personagem")
        draw_text(surface, "Nome", (panel.x + 28, panel.y + 60), COLORS["accent"], 18, bold=True)
        self.name_rect = pygame.Rect(panel.x + 28, panel.y + 86, 280, 38)
        pygame.draw.rect(surface, COLORS["panel_dark"], self.name_rect, border_radius=6)
        pygame.draw.rect(surface, COLORS["accent"] if self.name_active else (82, 92, 84), self.name_rect, 2, border_radius=6)
        draw_text(surface, self.name + ("|" if self.name_active else ""), (self.name_rect.x + 12, self.name_rect.y + 9), COLORS["white"], 17)

        self.class_buttons = []
        for index, class_id in enumerate(CLASS_ORDER):
            col = index % 2
            row = index // 2
            rect = pygame.Rect(panel.x + 28 + col * 175, panel.y + 150 + row * 62, 158, 46)
            button = Button(rect, CLASSES[class_id]["name"], ("class", class_id))
            button.hovered = class_id == self.selected_class
            button.draw(surface)
            self.class_buttons.append(button)

        preview = pygame.Rect(panel.x + 405, panel.y + 66, 590, 440)
        pygame.draw.rect(surface, COLORS["panel_dark"], preview, border_radius=6)
        pygame.draw.rect(surface, (82, 93, 86), preview, 1, border_radius=6)
        data = CLASSES[self.selected_class]
        draw_text(surface, data["name"], (preview.x + 24, preview.y + 18), COLORS["accent"], 28, bold=True)
        draw_wrapped(surface, data["description"], pygame.Rect(preview.x + 24, preview.y + 56, 350, 52), COLORS["white"], 16)
        frame = self.assets.player_frame(self.selected_class, "idle", "down", 0)
        scaled = pygame.transform.scale(frame, (108, 138))
        surface.blit(scaled, (preview.right - 165, preview.y + 42))
        weapon = data["weapon"].replace("_", " ").title()
        tool = data["tool"].replace("_", " ").title() if data.get("tool") else "Nenhuma"
        draw_text(surface, f"Arma inicial: {weapon}", (preview.x + 24, preview.y + 122), COLORS["white"], 16)
        draw_text(surface, f"Ferramenta inicial: {tool}", (preview.x + 24, preview.y + 148), COLORS["white"], 16)
        draw_text(surface, "Vantagens", (preview.x + 24, preview.y + 190), COLORS["accent"], 18, bold=True)
        for i, advantage in enumerate(data["advantages"][:5]):
            draw_text(surface, f"- {advantage}", (preview.x + 24, preview.y + 220 + i * 22), COLORS["white"], 14)
        draw_text(surface, "Desvantagens", (preview.x + 330, preview.y + 190), COLORS["accent"], 18, bold=True)
        for i, disadvantage in enumerate(data["disadvantages"][:4]):
            draw_text(surface, f"- {disadvantage}", (preview.x + 330, preview.y + 220 + i * 22), COLORS["white"], 14)
        draw_text(surface, "Skills principais", (preview.x + 24, preview.y + 350), COLORS["accent"], 18, bold=True)
        draw_wrapped(surface, ", ".join(data["skills"]), pygame.Rect(preview.x + 24, preview.y + 380, 530, 48), COLORS["white"], 15)

        self.buttons = [
            Button((panel.right - 320, panel.bottom - 62, 140, 40), "Voltar", "back"),
            Button((panel.right - 166, panel.bottom - 62, 138, 40), "Iniciar", "start"),
        ]
        for button in self.buttons:
            button.draw(surface)
