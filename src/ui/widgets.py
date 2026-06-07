from __future__ import annotations

import pygame

from src.core.settings import COLORS, Settings


def get_font(size: int = Settings.UI_FONT_SIZE, bold: bool = False) -> pygame.font.Font:
    return pygame.font.SysFont(Settings.UI_FONT, size, bold=bold)


def draw_text(surface: pygame.Surface, text: str, pos, color=COLORS["white"], size: int = Settings.UI_FONT_SIZE, bold: bool = False, center: bool = False) -> pygame.Rect:
    font = get_font(size, bold)
    image = font.render(str(text), True, color)
    rect = image.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surface.blit(image, rect)
    return rect


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    words = str(text).split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(surface: pygame.Surface, text: str, rect: pygame.Rect, color=COLORS["white"], size: int = Settings.UI_SMALL_FONT_SIZE, line_gap: int = 4) -> int:
    font = get_font(size)
    y = rect.y
    for line in wrap_text(text, font, rect.width):
        if y + font.get_height() > rect.bottom:
            break
        image = font.render(line, True, color)
        surface.blit(image, (rect.x, y))
        y += font.get_height() + line_gap
    return y


class Button:
    def __init__(self, rect, text: str, action: str | tuple, disabled: bool = False) -> None:
        self.rect = pygame.Rect(rect)
        self.text = text
        self.action = action
        self.disabled = disabled
        self.hovered = False

    def handle_event(self, event) -> str | tuple | None:
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.disabled and self.rect.collidepoint(event.pos):
                return self.action
        return None

    def draw(self, surface: pygame.Surface) -> None:
        if self.disabled:
            bg = (52, 55, 54)
            fg = (132, 136, 132)
            border = (74, 76, 73)
        elif self.hovered:
            bg = (74, 92, 82)
            fg = COLORS["white"]
            border = COLORS["accent"]
        else:
            bg = COLORS["panel_light"]
            fg = COLORS["white"]
            border = (80, 91, 84)
        pygame.draw.rect(surface, bg, self.rect, border_radius=6)
        pygame.draw.rect(surface, border, self.rect, 2, border_radius=6)
        draw_text(surface, self.text, self.rect.center, fg, Settings.UI_SMALL_FONT_SIZE, bold=True, center=True)


def draw_panel(surface: pygame.Surface, rect: pygame.Rect, title: str | None = None) -> None:
    pygame.draw.rect(surface, COLORS["panel"], rect, border_radius=8)
    pygame.draw.rect(surface, (77, 88, 80), rect, 2, border_radius=8)
    if title:
        draw_text(surface, title, (rect.x + 18, rect.y + 14), COLORS["accent"], 24, bold=True)
