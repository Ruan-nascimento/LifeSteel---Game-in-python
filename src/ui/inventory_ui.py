from __future__ import annotations

import pygame

from src.core.settings import COLORS
from src.data.items_data import ITEMS
from src.ui.widgets import Button, draw_panel, draw_text, draw_wrapped


class InventoryUI:
    def __init__(self, asset_loader) -> None:
        self.assets = asset_loader
        self.selected_ref: tuple[str, int] | None = ("main", 0)
        self.dragging_ref: tuple[str, int] | None = None
        self.buttons: list[Button] = []
        self.slot_rects: dict[tuple[str, int], pygame.Rect] = {}

    def handle_event(self, event, player) -> tuple | str | None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                action = button.handle_event(event)
                if action:
                    return action
            for ref, rect in self.slot_rects.items():
                if rect.collidepoint(event.pos):
                    self.selected_ref = ref
                    self.dragging_ref = ref
                    return None
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging_ref:
                target = self._slot_at(event.pos)
                source = self.dragging_ref
                self.dragging_ref = None
                if target and target != source:
                    self.selected_ref = target
                    return ("move_slot", source[0], source[1], target[0], target[1])
        if event.type == pygame.MOUSEMOTION:
            for button in self.buttons:
                button.handle_event(event)
        return None

    def _slot_at(self, pos) -> tuple[str, int] | None:
        for ref, rect in self.slot_rects.items():
            if rect.collidepoint(pos):
                return ref
        return None

    def draw(self, surface: pygame.Surface, player) -> None:
        width = min(1100, surface.get_width() - 48)
        height = min(620, surface.get_height() - 44)
        panel = pygame.Rect(surface.get_width() // 2 - width // 2, surface.get_height() // 2 - height // 2, width, height)
        draw_panel(surface, panel, "Inventario")
        self.buttons = []
        self.slot_rects = {}

        main_used = sum(1 for slot in player.inventory.slots if slot)
        draw_text(surface, f"Inventario: {main_used}/{player.inventory.capacity}", (panel.x + 24, panel.y + 50), COLORS["white"], 14)
        draw_text(surface, "Hotbar", (panel.x + 24, panel.y + 82), COLORS["accent"], 16, bold=True)
        self._draw_grid(surface, player.inventory.slots[:5], "main", 0, panel.x + 24, panel.y + 108, 5, player)
        draw_text(surface, "Mochila do personagem", (panel.x + 24, panel.y + 182), COLORS["accent"], 16, bold=True)
        self._draw_grid(surface, player.inventory.slots[5:], "main", 5, panel.x + 24, panel.y + 208, 5, player)

        backpack_slots = player.backpack_contents()
        backpack_x = panel.x + 394
        draw_text(surface, "Mochila equipada", (backpack_x, panel.y + 82), COLORS["accent"], 16, bold=True)
        if backpack_slots is not None:
            used = sum(1 for slot in backpack_slots if slot)
            draw_text(surface, f"Espaco: {used}/{len(backpack_slots)}", (backpack_x, panel.y + 50), COLORS["white"], 14)
            self._draw_grid(surface, backpack_slots, "backpack", 0, backpack_x, panel.y + 108, 4, player)
        else:
            empty = pygame.Rect(backpack_x, panel.y + 108, 250, 180)
            pygame.draw.rect(surface, COLORS["panel_dark"], empty, border_radius=6)
            pygame.draw.rect(surface, (71, 82, 76), empty, 1, border_radius=6)
            draw_wrapped(surface, "Equipe uma mochila para abrir os slots extras aqui. Se dropar a mochila, tudo dentro dela continua guardado no item caido.", empty.inflate(-24, -24), COLORS["white"], 14)

        self._draw_details(surface, panel, player)
        draw_text(surface, "Arraste itens entre inventario, hotbar e mochila. 1-5 seleciona hotbar.", (panel.x + 24, panel.bottom - 32), (178, 186, 174), 13)

    def _draw_grid(self, surface, slots, source: str, start_index: int, x: int, y: int, columns: int, player) -> None:
        slot_size = 54
        gap = 8
        rows = max(1, (len(slots) + columns - 1) // columns)
        for local_index in range(len(slots)):
            col = local_index % columns
            row = local_index // columns
            rect = pygame.Rect(x + col * (slot_size + gap), y + row * (slot_size + gap), slot_size, slot_size)
            absolute_index = start_index + local_index
            ref = (source, absolute_index)
            self.slot_rects[ref] = rect
            selected = self.selected_ref == ref
            slot = slots[local_index]
            pygame.draw.rect(surface, (64, 76, 70) if selected else COLORS["panel_dark"], rect, border_radius=6)
            border = COLORS["accent"] if selected else (75, 85, 78)
            if source == "main" and absolute_index == player.inventory.selected_slot:
                border = (235, 218, 120)
            if source == "main" and absolute_index == player.equipped_backpack_slot:
                border = (105, 190, 230)
            pygame.draw.rect(surface, border, rect, 2, border_radius=6)
            if source == "main" and absolute_index < 5:
                draw_text(surface, str(absolute_index + 1), (rect.x + 5, rect.y + 3), (187, 194, 183), 11, bold=True)
            if slot:
                icon = self.assets.item_icon(slot.item_id, 34)
                surface.blit(icon, (rect.centerx - 17, rect.centery - 17))
                if slot.quantity > 1:
                    draw_text(surface, str(slot.quantity), (rect.right - 18, rect.bottom - 18), COLORS["white"], 12, bold=True)
                if slot.is_container() and slot.contents is not None:
                    used = sum(1 for content in slot.contents if content)
                    draw_text(surface, str(used), (rect.x + 5, rect.bottom - 17), (105, 190, 230), 11, bold=True)
        total_width = columns * slot_size + (columns - 1) * gap
        total_height = rows * slot_size + (rows - 1) * gap
        pygame.draw.rect(surface, (48, 56, 52), (x - 6, y - 6, total_width + 12, total_height + 12), 1, border_radius=8)

    def _draw_details(self, surface, panel, player) -> None:
        details = pygame.Rect(panel.right - 360, panel.y + 84, 330, panel.height - 140)
        pygame.draw.rect(surface, COLORS["panel_dark"], details, border_radius=6)
        pygame.draw.rect(surface, (75, 86, 80), details, 1, border_radius=6)
        slot = self._selected_slot(player)
        if not slot:
            draw_text(surface, "Nenhum item selecionado.", (details.x + 18, details.y + 18), COLORS["white"], 16)
            return
        item = slot.item
        surface.blit(self.assets.item_icon(item.item_id, 48), (details.x + 18, details.y + 18))
        draw_text(surface, item.name, (details.x + 78, details.y + 18), COLORS["accent"], 19, bold=True)
        draw_text(surface, f"{item.category} | Qtd: {slot.quantity}", (details.x + 78, details.y + 44), COLORS["white"], 13)
        draw_wrapped(surface, item.description, pygame.Rect(details.x + 18, details.y + 86, details.width - 36, 90), COLORS["white"], 14)
        y = details.y + 184
        draw_text(surface, f"Preco base: {item.price} ZC", (details.x + 18, y), COLORS["white"], 14)
        y += 24
        if slot.is_container():
            contents = slot.ensure_contents()
            used = sum(1 for content in contents if content)
            draw_text(surface, f"Espaco interno: {used}/{len(contents)}", (details.x + 18, y), (105, 190, 230), 14, bold=True)
            y += 24
        if item.tool_type:
            draw_text(surface, f"Ferramenta: {item.tool_type}", (details.x + 18, y), COLORS["white"], 14)
            y += 24
        if item.is_weapon_like():
            draw_text(surface, f"Dano {item.damage} | Alcance {item.range}", (details.x + 18, y), COLORS["white"], 14)
            y += 24
        if item.is_building():
            draw_text(surface, "Equipe e clique no mundo para colocar.", (details.x + 18, y), COLORS["accent"], 13, bold=True)
        self._draw_action_buttons(surface, details, item)

    def _selected_slot(self, player):
        if not self.selected_ref:
            return None
        source, index = self.selected_ref
        if source == "main":
            if 0 <= index < player.inventory.capacity:
                return player.inventory.slots[index]
        elif source == "backpack":
            slots = player.backpack_contents()
            if slots is not None and 0 <= index < len(slots):
                return slots[index]
        return None

    def _draw_action_buttons(self, surface, details, item) -> None:
        if not self.selected_ref:
            return
        source, index = self.selected_ref
        actions = [
            ("Usar", ("use_slot", source, index), not item.is_consumable() and not item.data.get("container_slots")),
            ("Equipar", ("equip_slot", source, index), source != "main" or not (item.is_weapon_like() or item.is_building() or item.data.get("container_slots"))),
            ("Dropar", ("drop_slot", source, index), False),
        ]
        x = details.x + 18
        y = details.bottom - 48
        for label, action, disabled in actions:
            button = Button((x, y, 92, 32), label, action, disabled)
            button.draw(surface)
            self.buttons.append(button)
            x += 102
