from __future__ import annotations

import pygame

from src.core.settings import COLORS
from src.data.items_data import ITEMS
from src.ui.widgets import Button, draw_panel, draw_text, draw_wrapped


class ShopUI:
    def __init__(self, asset_loader) -> None:
        self.assets = asset_loader
        self.buttons: list[Button] = []

    def handle_event(self, event) -> tuple | None:
        if event.type in {pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION}:
            for button in self.buttons:
                action = button.handle_event(event)
                if action:
                    return action
        return None

    def draw(self, surface: pygame.Surface, player, shop_system) -> None:
        panel = pygame.Rect(surface.get_width() // 2 - 470, surface.get_height() // 2 - 290, 940, 580)
        draw_panel(surface, panel, "Loja da Clareira")
        draw_text(surface, f"Moedas: {player.coins} ZC", (panel.right - 170, panel.y + 20), COLORS["accent"], 17, bold=True)
        draw_text(surface, shop_system.message, (panel.x + 20, panel.y + 52), COLORS["white"], 14)

        left = pygame.Rect(panel.x + 20, panel.y + 84, 545, 450)
        right = pygame.Rect(panel.x + 585, panel.y + 84, 335, 450)
        pygame.draw.rect(surface, COLORS["panel_dark"], left, border_radius=6)
        pygame.draw.rect(surface, COLORS["panel_dark"], right, border_radius=6)
        pygame.draw.rect(surface, (74, 85, 78), left, 1, border_radius=6)
        pygame.draw.rect(surface, (74, 85, 78), right, 1, border_radius=6)
        draw_text(surface, "Comprar", (left.x + 12, left.y + 10), COLORS["accent"], 18, bold=True)
        draw_text(surface, "Vender", (right.x + 12, right.y + 10), COLORS["accent"], 18, bold=True)

        self.buttons = []
        y = left.y + 42
        for entry in shop_system.available_stock(player)[:10]:
            item_id = entry["id"]
            data = ITEMS[item_id]
            row = pygame.Rect(left.x + 10, y, left.width - 20, 38)
            pygame.draw.rect(surface, (34, 40, 38), row, border_radius=5)
            surface.blit(self.assets.item_icon(item_id, 26), (row.x + 7, row.y + 6))
            lock = " [bloq]" if entry["locked"] else ""
            draw_text(surface, f"{data['name']}{lock}", (row.x + 42, row.y + 6), COLORS["white"], 14, bold=True)
            draw_text(surface, f"{entry['final_price']} ZC | est. {entry.get('stock', 0)} | lvl {entry.get('required_level', 1)}", (row.x + 42, row.y + 22), (178, 187, 174), 12)
            button = Button((row.right - 82, row.y + 5, 70, 28), "Comprar", ("buy", item_id), disabled=entry["locked"] or entry.get("stock", 0) <= 0)
            button.draw(surface)
            self.buttons.append(button)
            y += 42

        sellable = [(i, slot) for i, slot in enumerate(player.inventory.slots) if slot and ITEMS[slot.item_id].get("price", 0) > 0]
        y = right.y + 42
        for slot_index, slot in sellable[:9]:
            row = pygame.Rect(right.x + 10, y, right.width - 20, 38)
            pygame.draw.rect(surface, (34, 40, 38), row, border_radius=5)
            surface.blit(self.assets.item_icon(slot.item_id, 24), (row.x + 6, row.y + 7))
            draw_text(surface, f"{ITEMS[slot.item_id]['name']} x{slot.quantity}", (row.x + 36, row.y + 7), COLORS["white"], 13, bold=True)
            button = Button((row.right - 78, row.y + 5, 66, 28), "Vender", ("sell", slot_index))
            button.draw(surface)
            self.buttons.append(button)
            y += 42

        info = pygame.Rect(panel.x + 20, panel.bottom - 38, panel.width - 40, 24)
        draw_wrapped(surface, "Comunicacao reduz preco de compra. Comercio e Politica aumentam preco de venda. A loja so abre perto do vendedor.", info, (183, 190, 178), 13)
