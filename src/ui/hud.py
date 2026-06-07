from __future__ import annotations

import pygame

from src.core.settings import COLORS, Settings
from src.data.items_data import ITEMS
from src.ui.minimap_ui import MinimapUI
from src.ui.widgets import draw_text


class HUD:
    def __init__(self, asset_loader) -> None:
        self.assets = asset_loader
        self.minimap = MinimapUI()

    def draw_bar(self, surface: pygame.Surface, pos, size, label: str, value: float, maximum: float, color) -> None:
        rect = pygame.Rect(pos, size)
        pygame.draw.rect(surface, COLORS["panel_dark"], rect, border_radius=4)
        ratio = 0 if maximum <= 0 else max(0, min(1, value / maximum))
        fill = rect.copy()
        fill.width = int(rect.width * ratio)
        pygame.draw.rect(surface, color, fill, border_radius=4)
        pygame.draw.rect(surface, (70, 77, 72), rect, 1, border_radius=4)
        draw_text(surface, f"{label}: {int(value)}/{int(maximum)}", (rect.x + 8, rect.y + 4), COLORS["white"], 13, bold=True)

    def draw(self, surface: pygame.Surface, player, world, exploration, npcs, enemies, time_system, weather_system, interaction_text: str | None, notifications, quest_system, show_fps: bool, fps: float) -> None:
        self.draw_bar(surface, (16, 16), (220, 22), "HP", player.hp, player.max_hp, COLORS["hp"])
        self.draw_bar(surface, (16, 43), (220, 18), "Fome", player.hunger, 100, COLORS["hunger"])
        self.draw_bar(surface, (16, 66), (220, 18), "Sede", player.thirst, 100, COLORS["thirst"])
        self.draw_bar(surface, (16, 89), (220, 18), "Energia", player.energy, player.max_energy, COLORS["energy"])
        self.draw_bar(surface, (16, 112), (220, 18), "Mana", player.mana, player.max_mana, COLORS["mana"])

        xp_rect = pygame.Rect(surface.get_width() // 2 - 180, 18, 360, 24)
        pygame.draw.rect(surface, COLORS["panel_dark"], xp_rect, border_radius=4)
        fill = xp_rect.copy()
        fill.width = int(xp_rect.width * (player.level.current_level_xp / player.level.xp_needed_this_level))
        pygame.draw.rect(surface, COLORS["xp"], fill, border_radius=4)
        pygame.draw.rect(surface, (75, 85, 84), xp_rect, 1, border_radius=4)
        draw_text(
            surface,
            f"Level {player.level.level} - XP {player.level.current_level_xp}/{player.level.xp_needed_this_level}",
            xp_rect.center,
            COLORS["white"],
            14,
            bold=True,
            center=True,
        )

        top_right = pygame.Rect(surface.get_width() - 250, 16, 232, 82)
        pygame.draw.rect(surface, (*COLORS["panel_dark"],), top_right, border_radius=6)
        pygame.draw.rect(surface, (75, 84, 78), top_right, 1, border_radius=6)
        draw_text(surface, f"{player.coins} ZC", (top_right.x + 12, top_right.y + 10), COLORS["accent"], 18, bold=True)
        draw_text(surface, time_system.clock_text(), (top_right.x + 12, top_right.y + 34), COLORS["white"], 15)
        draw_text(surface, f"Clima: {weather_system.current}", (top_right.x + 12, top_right.y + 56), COLORS["white"], 15)
        if show_fps:
            draw_text(surface, f"FPS {fps:.0f}", (top_right.x - 80, top_right.y + 8), COLORS["white"], 14)

        self._draw_hotbar(surface, player)
        self.minimap.draw(surface, world, exploration, player, npcs, enemies)
        if interaction_text:
            draw_text(surface, interaction_text, (surface.get_width() // 2, surface.get_height() - 118), COLORS["accent"], 17, bold=True, center=True)
        self._draw_quest(surface, quest_system)
        notifications.draw(surface)

    def _draw_hotbar(self, surface: pygame.Surface, player) -> None:
        slot_size = 58
        gap = 8
        total_width = Settings.HOTBAR_SIZE * slot_size + (Settings.HOTBAR_SIZE - 1) * gap
        x = surface.get_width() // 2 - total_width // 2
        y = surface.get_height() - slot_size - 18
        for i in range(Settings.HOTBAR_SIZE):
            rect = pygame.Rect(x + i * (slot_size + gap), y, slot_size, slot_size)
            selected = player.inventory.selected_slot == i
            bg = (64, 75, 69) if selected else COLORS["panel_dark"]
            pygame.draw.rect(surface, bg, rect, border_radius=6)
            pygame.draw.rect(surface, COLORS["accent"] if selected else (77, 86, 80), rect, 2, border_radius=6)
            slot = player.inventory.slots[i] if i < len(player.inventory.slots) else None
            draw_text(surface, str(i + 1), (rect.x + 5, rect.y + 3), (183, 190, 178), 12, bold=True)
            if slot:
                icon = self.assets.item_icon(slot.item_id, 34)
                surface.blit(icon, (rect.centerx - 17, rect.centery - 17))
                if slot.quantity > 1:
                    draw_text(surface, str(slot.quantity), (rect.right - 18, rect.bottom - 18), COLORS["white"], 12, bold=True)
            else:
                draw_text(surface, "Vazio", rect.center, (117, 124, 117), 11, center=True)

        item = player.equipped_item()
        label = item.name if item else "Maos vazias"
        draw_text(surface, label, (surface.get_width() // 2, y - 23), COLORS["white"], 14, bold=True, center=True)

    def _draw_quest(self, surface: pygame.Surface, quest_system) -> None:
        lines = quest_system.objective_lines()
        if not lines:
            return
        x = surface.get_width() - 248
        y = 108
        panel = pygame.Rect(x, y, 230, 94)
        pygame.draw.rect(surface, (*COLORS["panel_dark"],), panel, border_radius=6)
        pygame.draw.rect(surface, (72, 82, 76), panel, 1, border_radius=6)
        for index, line in enumerate(lines[:4]):
            color = COLORS["accent"] if index == 0 else COLORS["white"]
            draw_text(surface, line, (x + 10, y + 10 + index * 19), color, 12, bold=index == 0)
