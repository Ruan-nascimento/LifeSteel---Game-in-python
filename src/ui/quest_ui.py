from __future__ import annotations

import pygame

from src.core.settings import COLORS, Settings
from src.ui.widgets import Button, draw_panel, draw_text, draw_wrapped


STATUS_LABELS = {
    "active": "Ativa",
    "completed": "Pronta",
    "available": "Disponivel",
    "locked": "Bloqueada",
    "claimed": "Resgatada",
}


STATUS_COLORS = {
    "active": COLORS["accent"],
    "completed": COLORS["accent_2"],
    "available": COLORS["white"],
    "locked": (116, 122, 118),
    "claimed": (139, 148, 142),
}


class QuestUI:
    def __init__(self) -> None:
        self.buttons: list[Button] = []
        self.selected_id: str | None = None
        self.scroll = 0

    def handle_event(self, event, quest_system):
        if event.type == pygame.MOUSEWHEEL:
            total = len(quest_system.quests_for_ui())
            visible = Settings.MAX_VISIBLE_QUEST_ROWS
            self.scroll = max(0, min(max(0, total - visible), self.scroll - event.y))
            return None
        if event.type not in {pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION}:
            return None
        for button in self.buttons:
            action = button.handle_event(event)
            if not action:
                continue
            if isinstance(action, tuple) and action[0] == "select_quest":
                self.selected_id = action[1]
                return None
            return action
        return None

    def draw(self, surface: pygame.Surface, player, quest_system) -> None:
        width = min(1040, surface.get_width() - 56)
        height = min(640, surface.get_height() - 56)
        panel = pygame.Rect(surface.get_width() // 2 - width // 2, surface.get_height() // 2 - height // 2, width, height)
        draw_panel(surface, panel, "Missoes")
        self.buttons = []

        quests = quest_system.quests_for_ui()
        if quests and (not self.selected_id or self.selected_id not in quest_system.quest_defs):
            self.selected_id = quests[0][0].quest_id

        left = pygame.Rect(panel.x + 22, panel.y + 62, 360, panel.height - 124)
        right = pygame.Rect(left.right + 20, left.y, panel.right - left.right - 42, left.height)
        pygame.draw.rect(surface, COLORS["panel_dark"], left, border_radius=6)
        pygame.draw.rect(surface, (75, 86, 80), left, 1, border_radius=6)
        pygame.draw.rect(surface, COLORS["panel_dark"], right, border_radius=6)
        pygame.draw.rect(surface, (75, 86, 80), right, 1, border_radius=6)

        visible = Settings.MAX_VISIBLE_QUEST_ROWS
        self.scroll = max(0, min(max(0, len(quests) - visible), self.scroll))
        y = left.y + 12
        mouse_pos = pygame.mouse.get_pos()
        for quest, state in quests[self.scroll:self.scroll + visible]:
            row = pygame.Rect(left.x + 10, y, left.width - 20, 52)
            selected = quest.quest_id == self.selected_id
            hovered = row.collidepoint(mouse_pos)
            bg = (64, 74, 68) if selected else ((42, 49, 45) if hovered else (30, 35, 33))
            pygame.draw.rect(surface, bg, row, border_radius=5)
            pygame.draw.rect(surface, STATUS_COLORS.get(state.status, COLORS["white"]), row, 1, border_radius=5)
            draw_text(surface, quest.title[:31], (row.x + 10, row.y + 7), COLORS["white"], 14, bold=True)
            status = STATUS_LABELS.get(state.status, state.status)
            draw_text(surface, f"Lv {quest.level_required} | {status}", (row.x + 10, row.y + 29), STATUS_COLORS.get(state.status, COLORS["white"]), 12)
            self.buttons.append(Button(row, "", ("select_quest", quest.quest_id)))
            y += 58

        if len(quests) > visible:
            draw_text(surface, f"{self.scroll + 1}-{min(len(quests), self.scroll + visible)}/{len(quests)}", (left.right - 82, left.bottom + 10), (170, 178, 170), 12)

        self._draw_details(surface, right, player, quest_system)

        close = Button((panel.centerx - 70, panel.bottom - 46, 140, 34), "Fechar", "close_quests")
        close.draw(surface)
        self.buttons.append(close)

    def _draw_details(self, surface: pygame.Surface, rect: pygame.Rect, player, quest_system) -> None:
        if not self.selected_id:
            draw_text(surface, "Nenhuma missao selecionada.", (rect.x + 18, rect.y + 18), COLORS["white"], 16)
            return
        quest = quest_system.quest_defs.get(self.selected_id)
        state = quest_system.states.get(self.selected_id)
        if not quest or not state:
            draw_text(surface, "Missao inexistente.", (rect.x + 18, rect.y + 18), COLORS["white"], 16)
            return

        status = STATUS_LABELS.get(state.status, state.status)
        draw_text(surface, quest.title, (rect.x + 18, rect.y + 16), COLORS["accent"], 22, bold=True)
        draw_text(surface, f"Level {quest.level_required} | {status} | {quest.giver}", (rect.x + 18, rect.y + 48), STATUS_COLORS.get(state.status, COLORS["white"]), 13, bold=True)
        draw_wrapped(surface, quest.description, pygame.Rect(rect.x + 18, rect.y + 78, rect.width - 36, 62), COLORS["white"], 13)

        y = rect.y + 152
        draw_text(surface, "Objetivos", (rect.x + 18, y), COLORS["accent"], 17, bold=True)
        y += 30
        for objective, current, required in quest_system.objective_progress(quest, state):
            done = current >= required
            color = COLORS["accent_2"] if done else COLORS["white"]
            mark = "OK" if done else "--"
            draw_text(surface, f"{mark} {objective.label}: {current}/{required}", (rect.x + 24, y), color, 14, bold=done)
            y += 26

        y += 10
        draw_text(surface, "Recompensas", (rect.x + 18, y), COLORS["accent"], 17, bold=True)
        y += 30
        rewards = quest.rewards or {}
        reward_lines: list[str] = []
        if rewards.get("xp"):
            reward_lines.append(f"{int(rewards['xp'])} XP")
        if rewards.get("coins"):
            reward_lines.append(f"{int(rewards['coins'])} ZC")
        for skill in rewards.get("skill_xp", []):
            reward_lines.append(f"{skill.get('xp', 0)} XP em {skill.get('skill', '')}")
        for item in rewards.get("items", []) + quest.unique_rewards:
            item_id = item.get("id")
            item_name = quest_system_item_name(item_id)
            reward_lines.append(f"{item.get('quantity', 1)}x {item_name}")
        if not reward_lines:
            reward_lines.append("Sem recompensa material.")
        for line in reward_lines[:8]:
            draw_text(surface, line, (rect.x + 24, y), COLORS["white"], 13)
            y += 22

        can_accept = state.status == "available"
        can_claim = state.status == "completed"
        accept = Button((rect.x + 18, rect.bottom - 50, 118, 34), "Aceitar", ("accept_quest", quest.quest_id), disabled=not can_accept)
        claim = Button((rect.x + 150, rect.bottom - 50, 128, 34), "Resgatar", ("claim_quest", quest.quest_id), disabled=not can_claim)
        accept.draw(surface)
        claim.draw(surface)
        self.buttons.extend([accept, claim])

        if state.status == "locked":
            draw_text(surface, "Bloqueada por level ou progresso.", (rect.x + 294, rect.bottom - 42), (155, 160, 154), 13)
        elif state.status == "claimed":
            draw_text(surface, "Recompensa ja resgatada.", (rect.x + 294, rect.bottom - 42), (155, 160, 154), 13)


def quest_system_item_name(item_id: str | None) -> str:
    if not item_id:
        return "item"
    from src.data.items_data import ITEMS

    return ITEMS.get(str(item_id), {}).get("name", str(item_id))
