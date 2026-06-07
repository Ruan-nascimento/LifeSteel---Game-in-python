from __future__ import annotations

import pygame

from src.core.settings import COLORS
from src.data.classes_data import CLASSES
from src.data.skills_data import SKILL_DESCRIPTIONS
from src.ui.widgets import Button, draw_panel, draw_text, draw_wrapped


class CharacterUI:
    def __init__(self) -> None:
        self.tab = "status"
        self.buttons: list[Button] = []

    def handle_event(self, event) -> str | None:
        if event.type in {pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION}:
            for button in self.buttons:
                action = button.handle_event(event)
                if action:
                    self.tab = action
                    return action
        return None

    def draw(self, surface: pygame.Surface, player, quest_system) -> None:
        panel = pygame.Rect(surface.get_width() // 2 - 400, surface.get_height() // 2 - 270, 800, 540)
        draw_panel(surface, panel, "Personagem")
        self.buttons = []
        for idx, tab in enumerate(["status", "skills", "quests"]):
            button = Button((panel.x + 18 + idx * 104, panel.y + 54, 94, 30), tab.title(), tab)
            button.hovered = tab == self.tab
            button.draw(surface)
            self.buttons.append(button)
        if self.tab == "status":
            self._draw_status(surface, panel, player)
        elif self.tab == "skills":
            self._draw_skills(surface, panel, player)
        else:
            self._draw_quests(surface, panel, quest_system)

    def draw_skills_only(self, surface: pygame.Surface, player) -> None:
        panel = pygame.Rect(surface.get_width() // 2 - 430, surface.get_height() // 2 - 290, 860, 580)
        draw_panel(surface, panel, "Arvore de Habilidades")
        self._draw_skills(surface, panel, player, columns=3)

    def _draw_status(self, surface, panel, player) -> None:
        class_data = CLASSES[player.class_id]
        x = panel.x + 28
        y = panel.y + 104
        draw_text(surface, player.name, (x, y), COLORS["accent"], 26, bold=True)
        draw_text(surface, f"Classe: {class_data['name']}", (x, y + 36), COLORS["white"], 18)
        draw_text(surface, class_data["description"], (x, y + 64), COLORS["white"], 15)
        stats = [
            f"HP: {int(player.hp)}/{player.max_hp}",
            f"Fome: {int(player.hunger)}/100",
            f"Sede: {int(player.thirst)}/100",
            f"Energia: {int(player.energy)}/{player.max_energy}",
            f"Mana: {int(player.mana)}/{int(player.max_mana)}",
            f"Level: {player.level.level}",
            f"XP: {player.level.current_level_xp}/{player.level.xp_needed_this_level}",
            f"Moedas: {player.coins} ZC",
            f"Defesa: {player.defense}",
        ]
        for index, line in enumerate(stats):
            draw_text(surface, line, (x, y + 112 + index * 24), COLORS["white"], 16)
        status = player.status_effects or ["Inspirado"]
        draw_text(surface, "Status", (panel.x + 460, y), COLORS["accent"], 22, bold=True)
        for index, line in enumerate(status):
            draw_text(surface, line, (panel.x + 460, y + 34 + index * 24), COLORS["white"], 16)
        draw_text(surface, "Vantagens", (panel.x + 460, y + 148), COLORS["accent"], 18, bold=True)
        for index, line in enumerate(class_data["advantages"][:5]):
            draw_text(surface, f"- {line}", (panel.x + 460, y + 176 + index * 21), COLORS["white"], 14)
        draw_text(surface, "Desvantagens", (panel.x + 460, y + 292), COLORS["accent"], 18, bold=True)
        for index, line in enumerate(class_data["disadvantages"][:4]):
            draw_text(surface, f"- {line}", (panel.x + 460, y + 320 + index * 21), COLORS["white"], 14)

    def _draw_skills(self, surface, panel, player, columns: int = 2) -> None:
        skills = list(player.skills.skills.values())
        start_x = panel.x + 28
        start_y = panel.y + 104
        col_width = (panel.width - 56) // columns
        for index, skill in enumerate(skills):
            col = index % columns
            row = index // columns
            x = start_x + col * col_width
            y = start_y + row * 44
            if y > panel.bottom - 54:
                continue
            draw_text(surface, f"{skill.name} Lv {skill.level}", (x, y), COLORS["white"], 14, bold=True)
            bar = pygame.Rect(x, y + 20, col_width - 24, 9)
            pygame.draw.rect(surface, COLORS["panel_dark"], bar)
            fill = bar.copy()
            fill.width = int(bar.width * (skill.xp / skill.xp_to_next))
            pygame.draw.rect(surface, COLORS["accent_2"], fill)
            pygame.draw.rect(surface, (70, 81, 76), bar, 1)
        description_rect = pygame.Rect(panel.x + 28, panel.bottom - 36, panel.width - 56, 24)
        draw_wrapped(surface, "Skills evoluem por acao: combate, coleta, comercio, construcao, exploracao, magia e sobrevivencia.", description_rect, (180, 188, 176), 13)

    def _draw_quests(self, surface, panel, quest_system) -> None:
        lines = quest_system.objective_lines()
        x = panel.x + 28
        y = panel.y + 112
        if not lines:
            draw_text(surface, "Nenhuma missao ativa.", (x, y), COLORS["white"], 16)
            return
        for index, line in enumerate(lines):
            color = COLORS["accent"] if index == 0 else COLORS["white"]
            draw_text(surface, line, (x, y + index * 30), color, 17 if index == 0 else 15, bold=index == 0)
        draw_text(surface, quest_system.message, (x, panel.bottom - 48), COLORS["white"], 14)
