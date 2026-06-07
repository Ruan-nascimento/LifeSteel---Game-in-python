from __future__ import annotations

import pygame

from src.core.settings import COLORS
from src.data.items_data import ITEMS
from src.ui.widgets import Button, draw_panel, draw_text, draw_wrapped


class ShopUI:
    def __init__(self, asset_loader) -> None:
        self.assets = asset_loader
        self.buttons: list[Button] = []
        self.search = ""
        self.category = "Todos"
        self.scroll = 0

    def handle_event(self, event) -> tuple | None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.search = self.search[:-1]
                self.scroll = 0
                return None
            if event.key == pygame.K_ESCAPE:
                self.search = ""
                self.scroll = 0
                return None
            if event.unicode and event.unicode.isprintable():
                self.search = (self.search + event.unicode)[:32]
                self.scroll = 0
                return None
        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, self.scroll - event.y)
            return None
        if event.type in {pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION}:
            for button in self.buttons:
                action = button.handle_event(event)
                if action:
                    if isinstance(action, tuple) and action[0] == "shop_filter":
                        self.category = action[1]
                        self.scroll = 0
                        return None
                    if action == "clear_shop_search":
                        self.search = ""
                        self.scroll = 0
                        return None
                    return action
        return None

    def draw(self, surface: pygame.Surface, player, shop_system) -> None:
        panel = pygame.Rect(surface.get_width() // 2 - 470, surface.get_height() // 2 - 290, 940, 580)
        draw_panel(surface, panel, "Loja da Clareira")
        draw_text(surface, f"Moedas: {player.coins} ZC", (panel.right - 170, panel.y + 20), COLORS["accent"], 17, bold=True)
        draw_text(surface, shop_system.message, (panel.x + 20, panel.y + 52), COLORS["white"], 14)

        self.buttons = []
        search_rect = pygame.Rect(panel.x + 20, panel.y + 82, 390, 30)
        pygame.draw.rect(surface, COLORS["panel_dark"], search_rect, border_radius=5)
        pygame.draw.rect(surface, (74, 85, 78), search_rect, 1, border_radius=5)
        draw_text(surface, self.search or "Buscar por nome, tipo, raridade...", (search_rect.x + 10, search_rect.y + 7), (210, 203, 174), 13)
        clear = Button((search_rect.right + 8, search_rect.y, 70, 30), "Limpar", "clear_shop_search")
        clear.draw(surface)
        self.buttons.append(clear)

        filter_x = panel.x + 500
        filter_y = panel.y + 82
        for category_id, label in shop_system.categories():
            width = max(64, min(108, 20 + len(label) * 8))
            if filter_x + width > panel.right - 18:
                filter_x = panel.x + 500
                filter_y += 34
            button = Button((filter_x, filter_y, width, 30), label, ("shop_filter", category_id), disabled=self.category == category_id)
            button.draw(surface)
            self.buttons.append(button)
            filter_x += width + 6

        left = pygame.Rect(panel.x + 20, panel.y + 158, 545, 376)
        right = pygame.Rect(panel.x + 585, panel.y + 158, 335, 376)
        pygame.draw.rect(surface, COLORS["panel_dark"], left, border_radius=6)
        pygame.draw.rect(surface, COLORS["panel_dark"], right, border_radius=6)
        pygame.draw.rect(surface, (74, 85, 78), left, 1, border_radius=6)
        pygame.draw.rect(surface, (74, 85, 78), right, 1, border_radius=6)
        draw_text(surface, "Comprar", (left.x + 12, left.y + 10), COLORS["accent"], 18, bold=True)
        draw_text(surface, "Vender", (right.x + 12, right.y + 10), COLORS["accent"], 18, bold=True)

        y = left.y + 42
        mouse_pos = pygame.mouse.get_pos()
        hovered_item = None
        hovered_slot = None
        visible_stock = shop_system.available_stock(player, search=self.search, category=self.category, offset=self.scroll, limit=8)
        total_stock = shop_system.available_stock(player, search=self.search, category=self.category)
        for entry in visible_stock:
            item_id = entry["id"]
            data = ITEMS[item_id]
            row = pygame.Rect(left.x + 10, y, left.width - 20, 38)
            if row.collidepoint(mouse_pos):
                from src.items.item import make_item
                hovered_item = make_item(item_id)
            pygame.draw.rect(surface, (34, 40, 38), row, border_radius=5)
            surface.blit(self.assets.item_icon(item_id, 26), (row.x + 7, row.y + 6))
            lock = " [bloq]" if entry["locked"] else ""
            draw_text(surface, f"{data['name']}{lock}", (row.x + 42, row.y + 6), COLORS["white"], 14, bold=True)
            draw_text(surface, f"{entry['final_price']} ZC | est. {entry.get('stock', 0)} | lvl {entry.get('required_level', 1)}", (row.x + 42, row.y + 22), (178, 187, 174), 12)
            button = Button((row.right - 82, row.y + 5, 70, 28), "Comprar", ("buy", item_id), disabled=entry["locked"] or entry.get("stock", 0) <= 0)
            button.draw(surface)
            self.buttons.append(button)
            y += 42
        if len(total_stock) > 8:
            track = pygame.Rect(left.right - 8, left.y + 42, 4, left.height - 54)
            pygame.draw.rect(surface, (35, 43, 39), track, border_radius=2)
            handle_h = max(28, int(track.height * 8 / max(8, len(total_stock))))
            max_scroll = max(1, len(total_stock) - 8)
            handle_y = track.y + int((track.height - handle_h) * min(self.scroll, max_scroll) / max_scroll)
            pygame.draw.rect(surface, COLORS["accent"], (track.x, handle_y, track.width, handle_h), border_radius=2)

        sellable = []
        for i, slot in enumerate(player.inventory.slots):
            if not slot or ITEMS[slot.item_id].get("price", 0) <= 0 or not ITEMS[slot.item_id].get("sellable", True):
                continue
            if self.category != "Todos" and ITEMS[slot.item_id].get("type") != self.category and ITEMS[slot.item_id].get("category") != self.category:
                continue
            if self.search and not shop_system._matches_search(ITEMS[slot.item_id], self.search):
                continue
            sellable.append((i, slot))
        y = right.y + 42
        for slot_index, slot in sellable[:8]:
            row = pygame.Rect(right.x + 10, y, right.width - 20, 38)
            if row.collidepoint(mouse_pos):
                hovered_item = slot.item
                hovered_slot = slot
            pygame.draw.rect(surface, (34, 40, 38), row, border_radius=5)
            surface.blit(self.assets.item_icon(slot.item_id, 24), (row.x + 6, row.y + 7))
            draw_text(surface, f"{ITEMS[slot.item_id]['name']} x{slot.quantity}", (row.x + 36, row.y + 7), COLORS["white"], 13, bold=True)
            button = Button((row.right - 78, row.y + 5, 66, 28), "Vender", ("sell", slot_index))
            button.draw(surface)
            self.buttons.append(button)
            y += 42

        info = pygame.Rect(panel.x + 20, panel.bottom - 38, panel.width - 40, 24)
        draw_wrapped(surface, "Digite para pesquisar, use a roda do mouse para rolar e filtre por categoria. Comunicacao reduz compra; Comercio aumenta venda.", info, (183, 190, 178), 13)

        if hovered_item:
            from src.ui.widgets import draw_item_tooltip
            draw_item_tooltip(surface, hovered_item, mouse_pos, hovered_slot)
