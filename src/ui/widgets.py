from __future__ import annotations

from functools import lru_cache

import pygame

from src.core.settings import COLORS, Settings


@lru_cache(maxsize=64)
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


def draw_item_tooltip(surface: pygame.Surface, item, pos: tuple[int, int], slot=None) -> None:
    width = 280
    font_title = get_font(16, bold=True)
    font_body = get_font(13)
    
    lines = []
    lines.append((item.name, font_title, COLORS["accent"]))
    
    qty = f" | Qtd: {slot.quantity}" if slot and hasattr(slot, "quantity") and slot.quantity > 1 else ""
    lines.append((f"{item.category}{qty}", font_body, COLORS["white"]))
    
    if slot and hasattr(slot, "is_container") and slot.is_container():
        contents = slot.ensure_contents()
        used = sum(1 for c in contents if c)
        lines.append((f"Espaco: {used}/{len(contents)}", font_body, (105, 190, 230)))
    
    lines.append((f"Preco: {item.price} ZC", font_body, COLORS["white"]))
    
    if item.tool_type:
        lines.append((f"Ferramenta: {item.tool_type}", font_body, COLORS["white"]))
    if item.is_weapon_like():
        lines.append((f"Dano {item.damage} | Alcance {item.range}", font_body, COLORS["white"]))
    if slot and hasattr(slot, "max_durability") and slot.max_durability:
        current = slot.max_durability if slot.durability is None else int(slot.durability)
        maximum = int(slot.max_durability)
        ratio = current / max(1, maximum)
        state = "Bom"
        state_color = COLORS["accent_2"]
        if ratio <= 0.10:
            state = "Muito danificado"
            state_color = COLORS["danger"]
        elif ratio <= 0.25:
            state = "Quase quebrando"
            state_color = COLORS["energy"]
        lines.append((f"Durabilidade: {current}/{maximum}", font_body, COLORS["white"]))
        lines.append((f"Estado: {int(ratio * 100)}% - {state}", font_body, state_color))
    if item.is_building():
        lines.append(("Equipe e clique no mundo para colocar", font_body, COLORS["accent"]))
        
    if "heal" in item.data:
        lines.append((f"Recupera {item.data['heal']} Vida", font_body, COLORS["hp"]))
    if "hunger" in item.data:
        lines.append((f"Recupera {item.data['hunger']} Fome", font_body, COLORS["hunger"]))
    if "thirst" in item.data:
        lines.append((f"Recupera {item.data['thirst']} Sede", font_body, COLORS["thirst"]))
    if "energy" in item.data:
        lines.append((f"Recupera {item.data['energy']} Energia", font_body, COLORS["energy"]))
    if "mana" in item.data:
        lines.append((f"Recupera {item.data['mana']} Mana", font_body, COLORS["mana"]))
        
    wrapped_desc = wrap_text(item.description, font_body, width - 24)
    
    height = 24
    for text, font, color in lines:
        height += font.get_height() + 2
    if wrapped_desc:
        height += 8
        for text in wrapped_desc:
            height += font_body.get_height() + 2
            
    x, y = pos
    x += 16
    y += 16
    
    sw, sh = surface.get_size()
    if x + width > sw:
        x = pos[0] - width - 8
    if y + height > sh:
        y = sh - height - 8
        
    rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, (28, 34, 30), rect, border_radius=6)
    pygame.draw.rect(surface, (88, 98, 92), rect, 1, border_radius=6)
    
    cy = y + 12
    for text, font, color in lines:
        img = font.render(text, True, color)
        surface.blit(img, (x + 12, cy))
        cy += font.get_height() + 2
        
    if wrapped_desc:
        cy += 8
        for text in wrapped_desc:
            img = font_body.render(text, True, (210, 218, 212))
            surface.blit(img, (x + 12, cy))
            cy += font_body.get_height() + 2

def _get_skill_bonus_text(name: str, level: int) -> str:
    if name == "Comunicacao":
        val = min(0.25, (level - 1) * 0.04)
        return f"{int(val * 100)}% desconto em compras"
    if name == "Comercio":
        val = min(0.30, (level - 1) * 0.05)
        return f"+{int(val * 100)}% valor de venda"
    if name == "Exploracao":
        val = (level - 1) * 18
        return f"+{val}px raio de visao no mapa"
    if name == "Construcao":
        val = min(0.20, (level - 1) * 0.035)
        return f"{int(val * 100)}% desconto em material"
    if name == "Politica":
        val = (level - 1) * 0.02
        return f"+{int(val * 100)}% valor de venda adicional"
    if name == "Combate":
        return f"+{level * 2}% de dano (estimado)"
    if name == "Defesa":
        return f"-{level * 1.5}% de dano recebido (estimado)"
    if name == "Magia":
        return f"+{level * 2}% de dano magico (estimado)"
    return f"+{level}% eficiencia geral"

def draw_skill_tooltip(surface: pygame.Surface, skill, pos: tuple[int, int]) -> None:
    from src.data.skills_data import SKILL_DESCRIPTIONS
    desc = SKILL_DESCRIPTIONS.get(skill.name, "Melhora habilidades e atributos relacionados.")
    current_bonus = _get_skill_bonus_text(skill.name, skill.level)
    next_bonus = _get_skill_bonus_text(skill.name, skill.level + 1)
    
    width = 280
    font_title = get_font(16, bold=True)
    font_body = get_font(13)
    
    lines = []
    lines.append((f"{skill.name} Lv {skill.level}", font_title, COLORS["accent"]))
    lines.append((f"Atual: {current_bonus}", font_body, COLORS["white"]))
    lines.append((f"Proximo: {next_bonus}", font_body, (180, 188, 176)))
    
    wrapped_desc = wrap_text(desc, font_body, width - 24)
    height = 24
    for text, font, color in lines:
        height += font.get_height() + 2
    if wrapped_desc:
        height += 8
        for text in wrapped_desc:
            height += font_body.get_height() + 2
            
    x, y = pos
    x += 16
    y += 16
    
    sw, sh = surface.get_size()
    if x + width > sw:
        x = pos[0] - width - 8
    if y + height > sh:
        y = sh - height - 8
        
    rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, (28, 34, 30), rect, border_radius=6)
    pygame.draw.rect(surface, (88, 98, 92), rect, 1, border_radius=6)
    
    cy = y + 12
    for text, font, color in lines:
        img = font.render(text, True, color)
        surface.blit(img, (x + 12, cy))
        cy += font.get_height() + 2
        
    if wrapped_desc:
        cy += 8
        for text in wrapped_desc:
            img = font_body.render(text, True, (210, 218, 212))
            surface.blit(img, (x + 12, cy))
            cy += font_body.get_height() + 2
