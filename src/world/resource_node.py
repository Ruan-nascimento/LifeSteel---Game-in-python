from __future__ import annotations

import random
from dataclasses import dataclass, field

import pygame

from src.core.settings import Settings


RESOURCE_DATA = {
    "tree": {
        "hp": 36,
        "required_tool": "axe",
        "drops": {"wood": (3, 6), "stick": (1, 3), "apple": (0, 1)},
        "xp": 1,
        "skill": "Lenhador",
        "particle": (58, 142, 66),
        "solid": True,
    },
    "stone": {
        "hp": 30,
        "required_tool": "pickaxe",
        "drops": {"stone": (3, 5), "simple_ore": (0, 1)},
        "xp": 3,
        "skill": "Mineracao",
        "particle": (135, 140, 140),
        "solid": True,
    },
    "ore": {
        "hp": 42,
        "required_tool": "pickaxe",
        "drops": {"stone": (1, 2), "simple_ore": (1, 3), "copper_ore": (0, 1)},
        "xp": 5,
        "skill": "Mineracao",
        "particle": (198, 121, 62),
        "solid": True,
    },
    "bush": {
        "hp": 10,
        "required_tool": None,
        "drops": {"fiber": (1, 3), "herb": (0, 1), "mushroom": (0, 1)},
        "xp": 1,
        "skill": "Coleta",
        "particle": (80, 160, 80),
        "solid": False,
    },
    "soil": {
        "hp": 8,
        "required_tool": "dig",
        "drops": {"basic_seed": (0, 2), "fiber": (0, 1)},
        "xp": 1,
        "skill": "Agricultura",
        "particle": (135, 92, 54),
        "solid": False,
    },
}


@dataclass
class ResourceNode:
    kind: str
    tile_x: int
    tile_y: int
    hp: int = field(init=False)

    def __post_init__(self) -> None:
        self.hp = RESOURCE_DATA[self.kind]["hp"]

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.tile_x * Settings.TILE_SIZE,
            self.tile_y * Settings.TILE_SIZE,
            Settings.TILE_SIZE,
            Settings.TILE_SIZE,
        )

    @property
    def center(self) -> pygame.Vector2:
        return pygame.Vector2(self.rect.center)

    @property
    def required_tool(self) -> str | None:
        return RESOURCE_DATA[self.kind]["required_tool"]

    @property
    def solid(self) -> bool:
        return RESOURCE_DATA[self.kind]["solid"]

    @property
    def particle_color(self) -> tuple[int, int, int]:
        return RESOURCE_DATA[self.kind]["particle"]

    @property
    def skill_name(self) -> str:
        return RESOURCE_DATA[self.kind]["skill"]

    @property
    def xp_reward(self) -> int:
        return RESOURCE_DATA[self.kind]["xp"]

    def can_harvest_with(self, item) -> bool:
        required = self.required_tool
        if required is None:
            return True
        if required == "dig":
            return item.tool_type in {"shovel", "hoe"}
        return item.tool_type == required

    def harvest(self, power: int) -> dict[str, int]:
        self.hp -= max(1, power)
        if self.hp > 0:
            return {}
        drops = {}
        for item_id, (minimum, maximum) in RESOURCE_DATA[self.kind]["drops"].items():
            amount = random.randint(minimum, maximum)
            if amount > 0:
                drops[item_id] = amount
        return drops
