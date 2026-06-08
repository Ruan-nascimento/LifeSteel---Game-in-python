from __future__ import annotations

import math
from functools import lru_cache

import pygame

from src.core.settings import COLORS, Settings
from src.data.animals_data import ANIMAL_TYPES
from src.data.classes_data import CLASSES
from src.data.enemies_data import ENEMY_TYPES
from src.data.items_data import ITEMS


class AssetLoader:
    def __init__(self) -> None:
        self.tile_size = Settings.TILE_SIZE
        self.tiles = self._build_tiles()
        self.resources = self._build_resources()
        self.buildings = self._build_buildings()
        self.enemies = self._build_enemies()
        self.animals = self._build_animals()
        self.npcs = self._build_npcs()

    def _surface(self, size, color=None) -> pygame.Surface:
        surface = pygame.Surface(size, pygame.SRCALPHA)
        if color:
            surface.fill(color)
        return surface

    def _build_tiles(self) -> dict[str, pygame.Surface]:
        size = self.tile_size
        tiles = {}
        for name, color in [
            ("grass", COLORS["grass"]),
            ("grass_dark", COLORS["grass_dark"]),
            ("grass_light", COLORS["grass_light"]),
            ("soil", COLORS["soil"]),
            ("path", COLORS["path"]),
            ("water", COLORS["water"]),
        ]:
            surf = self._surface((size, size), color)
            if name.startswith("grass"):
                pygame.draw.line(surf, (color[0] + 12, min(255, color[1] + 12), color[2]), (4, 25), (10, 19), 1)
                pygame.draw.line(surf, (max(0, color[0] - 15), color[1], color[2]), (22, 6), (28, 12), 1)
            if name == "water":
                pygame.draw.arc(surf, (94, 165, 205), (3, 8, 24, 12), 0, math.pi, 2)
            if name == "path":
                pygame.draw.circle(surf, (154, 135, 88), (9, 11), 2)
                pygame.draw.circle(surf, (100, 88, 62), (22, 23), 2)
            tiles[name] = surf
        return tiles

    def _build_resources(self) -> dict[str, pygame.Surface]:
        size = self.tile_size
        resources = {}
        tree = self._surface((size, size + 18))
        pygame.draw.rect(tree, (105, 69, 38), (13, 22, 7, 22))
        pygame.draw.circle(tree, (35, 111, 54), (16, 18), 16)
        pygame.draw.circle(tree, (52, 137, 65), (8, 25), 10)
        pygame.draw.circle(tree, (51, 132, 61), (24, 24), 10)
        resources["tree"] = tree

        stone = self._surface((size, size))
        pygame.draw.polygon(stone, (105, 113, 116), [(5, 24), (12, 10), (24, 8), (29, 22), (20, 29), (9, 28)])
        pygame.draw.line(stone, (139, 148, 150), (12, 10), (18, 27), 2)
        resources["stone"] = stone

        ore = stone.copy()
        pygame.draw.circle(ore, (193, 111, 58), (19, 17), 4)
        pygame.draw.circle(ore, (232, 143, 73), (11, 23), 3)
        resources["ore"] = ore

        bush = self._surface((size, size))
        pygame.draw.circle(bush, (54, 126, 52), (13, 18), 10)
        pygame.draw.circle(bush, (71, 150, 61), (21, 19), 9)
        pygame.draw.circle(bush, (177, 48, 55), (17, 16), 2)
        resources["bush"] = bush

        soil = self._surface((size, size))
        pygame.draw.ellipse(soil, (104, 75, 48), (4, 10, 24, 15))
        pygame.draw.line(soil, (145, 102, 64), (8, 17), (24, 17), 1)
        resources["soil"] = soil
        return resources

    def _build_buildings(self) -> dict[str, pygame.Surface]:
        size = self.tile_size
        result = {}
        campfire = self._surface((size, size))
        pygame.draw.line(campfire, (94, 58, 32), (8, 24), (24, 16), 5)
        pygame.draw.line(campfire, (94, 58, 32), (8, 16), (24, 24), 5)
        pygame.draw.polygon(campfire, (235, 92, 44), [(16, 8), (10, 22), (22, 22)])
        pygame.draw.polygon(campfire, (249, 190, 68), [(16, 12), (13, 22), (20, 22)])
        result["campfire"] = campfire

        chest = self._surface((size, size))
        pygame.draw.rect(chest, (122, 78, 42), (5, 11, 22, 15), border_radius=3)
        pygame.draw.rect(chest, (85, 53, 31), (5, 11, 22, 15), 2, border_radius=3)
        pygame.draw.rect(chest, (219, 171, 73), (14, 16, 4, 5))
        result["chest"] = chest

        workbench = self._surface((size, size))
        pygame.draw.rect(workbench, (116, 76, 48), (4, 9, 24, 16))
        pygame.draw.rect(workbench, (83, 52, 33), (4, 9, 24, 16), 2)
        pygame.draw.line(workbench, (161, 104, 60), (6, 14), (26, 14), 2)
        result["workbench"] = workbench

        stove = self._surface((size, size))
        pygame.draw.rect(stove, (96, 98, 95), (5, 8, 22, 20), border_radius=3)
        pygame.draw.rect(stove, (47, 49, 47), (5, 8, 22, 20), 2, border_radius=3)
        pygame.draw.circle(stove, (32, 34, 33), (16, 18), 6)
        pygame.draw.circle(stove, (234, 104, 55), (16, 18), 3)
        pygame.draw.rect(stove, (77, 78, 75), (10, 4, 12, 6), border_radius=2)
        result["stone_stove"] = stove

        torch = self._surface((size, size))
        pygame.draw.line(torch, (89, 55, 31), (16, 13), (16, 29), 4)
        pygame.draw.circle(torch, (238, 167, 55), (16, 10), 6)
        result["torch"] = torch

        fence = self._surface((size, size))
        pygame.draw.line(fence, (124, 82, 46), (5, 12), (27, 12), 4)
        pygame.draw.line(fence, (124, 82, 46), (5, 22), (27, 22), 4)
        pygame.draw.line(fence, (96, 62, 37), (10, 7), (10, 28), 4)
        pygame.draw.line(fence, (96, 62, 37), (22, 7), (22, 28), 4)
        result["fence"] = fence

        floor = self._surface((size, size), (143, 98, 55))
        pygame.draw.line(floor, (116, 78, 44), (0, 10), (32, 10), 2)
        pygame.draw.line(floor, (116, 78, 44), (0, 22), (32, 22), 2)
        result["wood_floor"] = floor

        wall = self._surface((size, size), (119, 79, 46))
        pygame.draw.rect(wall, (83, 52, 34), (0, 0, size, size), 2)
        result["wall"] = wall

        bed = self._surface((size, size))
        pygame.draw.rect(bed, (100, 67, 45), (5, 8, 22, 18))
        pygame.draw.rect(bed, (178, 75, 86), (7, 10, 18, 12))
        pygame.draw.rect(bed, (229, 218, 184), (8, 11, 7, 6))
        result["bed"] = bed

        shelter = self._surface((size * 2, size * 2))
        pygame.draw.rect(shelter, (111, 73, 45), (11, 28, 42, 26))
        pygame.draw.polygon(shelter, (86, 56, 35), [(7, 30), (32, 8), (57, 30)])
        pygame.draw.rect(shelter, (56, 38, 26), (28, 39, 9, 15))
        result["shelter"] = shelter
        return result

    def _build_enemies(self) -> dict[str, pygame.Surface]:
        result = {}
        for kind, data in ENEMY_TYPES.items():
            color = data["color"]
            surface = self._surface((34, 30))
            if kind == "forest_slime":
                pygame.draw.ellipse(surface, color, (2, 8, 30, 18))
                pygame.draw.circle(surface, (218, 242, 214), (12, 17), 2)
                pygame.draw.circle(surface, (218, 242, 214), (22, 17), 2)
            elif kind == "young_wolf":
                pygame.draw.ellipse(surface, color, (5, 12, 24, 12))
                pygame.draw.polygon(surface, color, [(23, 13), (31, 8), (29, 18)])
                pygame.draw.polygon(surface, (83, 83, 78), [(10, 11), (14, 4), (17, 12)])
                pygame.draw.circle(surface, (18, 18, 18), (27, 13), 2)
            elif kind == "forest_bat":
                pygame.draw.polygon(surface, color, [(16, 14), (1, 5), (7, 20)])
                pygame.draw.polygon(surface, color, [(18, 14), (33, 5), (27, 20)])
                pygame.draw.ellipse(surface, (65, 51, 83), (11, 10, 12, 13))
                pygame.draw.circle(surface, (230, 230, 222), (15, 14), 1)
                pygame.draw.circle(surface, (230, 230, 222), (20, 14), 1)
            elif kind == "thorn_plant":
                pygame.draw.circle(surface, color, (17, 17), 11)
                for point in [(17, 3), (5, 12), (29, 12), (9, 25), (25, 25)]:
                    pygame.draw.line(surface, (190, 222, 128), (17, 17), point, 2)
                pygame.draw.circle(surface, (90, 28, 42), (17, 17), 4)
            elif kind == "water_sprite":
                pygame.draw.circle(surface, color, (17, 15), 12)
                pygame.draw.arc(surface, (164, 225, 244), (6, 8, 22, 16), 0, math.pi, 2)
                pygame.draw.circle(surface, (224, 248, 255), (13, 14), 2)
                pygame.draw.circle(surface, (224, 248, 255), (21, 14), 2)
            elif kind == "mud_crab":
                pygame.draw.ellipse(surface, color, (6, 10, 22, 15))
                pygame.draw.circle(surface, (225, 150, 86), (6, 15), 5)
                pygame.draw.circle(surface, (225, 150, 86), (28, 15), 5)
                pygame.draw.circle(surface, (32, 24, 18), (13, 12), 1)
                pygame.draw.circle(surface, (32, 24, 18), (21, 12), 1)
            elif kind == "ice_wisp":
                pygame.draw.polygon(surface, color, [(17, 2), (28, 14), (20, 28), (8, 24), (5, 11)])
                pygame.draw.polygon(surface, (231, 252, 255), [(17, 7), (23, 15), (18, 22), (11, 19), (10, 12)])
            else:
                pygame.draw.ellipse(surface, color, (4, 7, 26, 20))
                pygame.draw.circle(surface, (235, 232, 218), (13, 15), 2)
                pygame.draw.circle(surface, (235, 232, 218), (21, 15), 2)
                if data.get("ranged"):
                    pygame.draw.line(surface, (220, 215, 185), (17, 6), (28, 2), 2)
            result[kind] = surface
        return result

    def _build_animals(self) -> dict[str, pygame.Surface]:
        result = {}
        for kind, data in ANIMAL_TYPES.items():
            color = data["color"]
            surface = self._surface((34, 26))
            if kind == "pig":
                pygame.draw.ellipse(surface, color, (5, 8, 24, 13))
                pygame.draw.circle(surface, color, (25, 12), 7)
                pygame.draw.circle(surface, (224, 154, 160), (28, 13), 3)
                pygame.draw.circle(surface, (50, 34, 35), (24, 10), 1)
            elif kind == "cow":
                pygame.draw.ellipse(surface, color, (4, 8, 25, 14))
                pygame.draw.rect(surface, (71, 62, 55), (10, 10, 6, 6), border_radius=2)
                pygame.draw.circle(surface, color, (27, 12), 7)
                pygame.draw.circle(surface, (39, 34, 30), (29, 11), 1)
                pygame.draw.line(surface, (75, 57, 42), (25, 6), (22, 2), 2)
                pygame.draw.line(surface, (75, 57, 42), (29, 6), (32, 2), 2)
            elif kind == "chicken":
                pygame.draw.ellipse(surface, color, (8, 9, 17, 12))
                pygame.draw.circle(surface, color, (23, 10), 6)
                pygame.draw.polygon(surface, (222, 143, 47), [(29, 10), (34, 12), (29, 14)])
                pygame.draw.circle(surface, (36, 30, 25), (24, 9), 1)
                pygame.draw.circle(surface, (206, 52, 45), (21, 4), 3)
            result[kind] = surface
        return result

    def _build_npcs(self) -> dict[str, pygame.Surface]:
        vendor = self._surface((28, 40))
        pygame.draw.circle(vendor, (213, 167, 115), (14, 8), 7)
        pygame.draw.rect(vendor, (72, 109, 157), (7, 15, 14, 18))
        pygame.draw.rect(vendor, (224, 181, 74), (5, 14, 18, 4))
        pygame.draw.line(vendor, (70, 45, 32), (9, 34), (7, 39), 3)
        pygame.draw.line(vendor, (70, 45, 32), (19, 34), (21, 39), 3)
        return {"vendor": vendor}

    @lru_cache(maxsize=256)
    def item_icon(self, item_id: str, size: int = 26) -> pygame.Surface:
        color = ITEMS.get(item_id, {}).get("icon_color", (240, 240, 240))
        surface = self._surface((size, size))
        inset = pygame.Rect(4, 4, size - 8, size - 8)
        item_type = ITEMS.get(item_id, {}).get("type")
        if item_id == "apple":
            pygame.draw.circle(surface, color, inset.center, max(4, size // 4))
            pygame.draw.line(surface, (73, 47, 28), (inset.centerx, inset.y + 2), (inset.centerx + 3, inset.y - 2), 2)
            pygame.draw.ellipse(surface, (80, 166, 75), (inset.centerx + 2, inset.y, 7, 4))
        elif "sword" in item_id or "dagger" in item_id:
            pygame.draw.line(surface, (226, 231, 226), (inset.x + 4, inset.bottom - 4), (inset.right - 4, inset.y + 4), 4)
            pygame.draw.line(surface, color, (inset.x + 5, inset.bottom - 5), (inset.x + 12, inset.bottom - 12), 5)
        elif "axe" in item_id:
            pygame.draw.line(surface, (90, 55, 32), (inset.x + 5, inset.bottom - 2), (inset.right - 6, inset.y + 4), 4)
            pygame.draw.polygon(surface, color, [(inset.right - 10, inset.y + 2), (inset.right, inset.y + 8), (inset.right - 8, inset.y + 15)])
        elif "pickaxe" in item_id:
            pygame.draw.line(surface, (88, 55, 34), (inset.x + 8, inset.bottom - 2), (inset.right - 8, inset.y + 5), 4)
            pygame.draw.arc(surface, color, (inset.x + 5, inset.y + 2, inset.width, inset.height // 2), math.pi, math.tau, 3)
        elif "shovel" in item_id or "hoe" in item_id:
            pygame.draw.line(surface, (91, 58, 34), (inset.x + 7, inset.bottom - 3), (inset.right - 7, inset.y + 5), 4)
            pygame.draw.ellipse(surface, color, (inset.right - 11, inset.y + 2, 9, 10))
        elif "staff" in item_id:
            pygame.draw.line(surface, (113, 73, 43), (inset.x + 6, inset.bottom - 3), (inset.right - 6, inset.y + 4), 4)
            pygame.draw.circle(surface, color, (inset.right - 6, inset.y + 4), 5)
        elif "backpack" in item_id:
            pygame.draw.rect(surface, color, (inset.x + 3, inset.y + 4, inset.width - 6, inset.height - 4), border_radius=4)
            pygame.draw.rect(surface, (69, 43, 25), (inset.x + 7, inset.y + 1, inset.width - 14, 7), border_radius=3)
            pygame.draw.line(surface, (230, 190, 98), (inset.x + 6, inset.centery), (inset.right - 6, inset.centery), 2)
        elif item_id in {"water_cup", "empty_cup"}:
            pygame.draw.rect(surface, (214, 225, 223), (inset.x + 6, inset.y + 4, inset.width - 12, inset.height - 5), border_radius=3)
            pygame.draw.rect(surface, (72, 88, 89), (inset.x + 6, inset.y + 4, inset.width - 12, inset.height - 5), 2, border_radius=3)
            if item_id == "water_cup":
                pygame.draw.rect(surface, (72, 169, 224), (inset.x + 8, inset.centery, inset.width - 16, inset.height // 3), border_radius=2)
            pygame.draw.arc(surface, (72, 88, 89), (inset.right - 8, inset.y + 8, 8, 10), -1.2, 1.2, 2)
        elif item_type == "drink":
            pygame.draw.rect(surface, (218, 230, 232), (inset.x + 7, inset.y + 4, inset.width - 14, inset.height - 6), border_radius=4)
            pygame.draw.rect(surface, (73, 86, 92), (inset.x + 7, inset.y + 4, inset.width - 14, inset.height - 6), 2, border_radius=4)
            pygame.draw.rect(surface, color, (inset.x + 9, inset.centery, inset.width - 18, inset.height // 3), border_radius=2)
            pygame.draw.line(surface, (232, 232, 205), (inset.centerx + 4, inset.y), (inset.centerx + 8, inset.y + 14), 2)
        elif item_type == "potion":
            pygame.draw.rect(surface, (196, 205, 214), (inset.centerx - 4, inset.y + 2, 8, 7), border_radius=2)
            pygame.draw.polygon(surface, color, [(inset.centerx, inset.y + 8), (inset.x + 5, inset.bottom - 4), (inset.right - 5, inset.bottom - 4)])
            pygame.draw.polygon(surface, (238, 242, 240), [(inset.centerx, inset.y + 10), (inset.x + 10, inset.bottom - 7), (inset.right - 10, inset.bottom - 7)], 1)
        elif item_id in {"campfire", "torch"}:
            pygame.draw.line(surface, (96, 58, 32), (inset.x + 5, inset.bottom - 3), (inset.right - 5, inset.bottom - 9), 4)
            pygame.draw.polygon(surface, (236, 89, 45), [(inset.centerx, inset.y + 2), (inset.x + 7, inset.bottom - 5), (inset.right - 7, inset.bottom - 5)])
            pygame.draw.polygon(surface, (249, 190, 66), [(inset.centerx, inset.y + 7), (inset.x + 11, inset.bottom - 6), (inset.right - 11, inset.bottom - 6)])
        elif item_id == "stone_stove":
            pygame.draw.rect(surface, color, (inset.x + 2, inset.y + 4, inset.width - 4, inset.height - 4), border_radius=3)
            pygame.draw.circle(surface, (35, 35, 34), inset.center, max(4, size // 6))
            pygame.draw.circle(surface, (226, 93, 50), inset.center, max(2, size // 10))
        elif item_type == "food":
            pygame.draw.ellipse(surface, color, (inset.x + 3, inset.y + 6, inset.width - 6, inset.height - 9))
            pygame.draw.circle(surface, (255, 236, 168), (inset.right - 7, inset.y + 7), 3)
        elif item_type == "building":
            pygame.draw.rect(surface, color, inset, border_radius=3)
            pygame.draw.line(surface, (44, 46, 44), inset.topleft, inset.bottomright, 2)
        elif item_type == "material":
            pygame.draw.polygon(surface, color, [(inset.x + 2, inset.bottom - 4), (inset.centerx, inset.y + 2), (inset.right - 2, inset.bottom - 4)])
        else:
            pygame.draw.rect(surface, color, inset, border_radius=4)
        return surface

    def player_frame(self, class_id: str, state: str, direction: str, frame: int) -> pygame.Surface:
        color = CLASSES[class_id]["sprite_color"]
        surface = self._surface((36, 46))
        bob = 0
        if state in {"walk", "run"}:
            bob = -1 if frame % 2 == 0 else 1
        if state == "attack":
            bob = -2
        shadow = pygame.Surface((28, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 70), (0, 0, 28, 8))
        surface.blit(shadow, (4, 36))
        pygame.draw.circle(surface, (212, 166, 118), (18, 11 + bob), 7)
        pygame.draw.rect(surface, color, (10, 18 + bob, 16, 17), border_radius=4)
        pygame.draw.rect(surface, (34, 35, 34), (12, 34 + bob, 5, 8))
        pygame.draw.rect(surface, (34, 35, 34), (20, 34 + bob, 5, 8))
        if direction == "left":
            pygame.draw.rect(surface, color, (5, 21 + bob, 8, 5))
            pygame.draw.circle(surface, (35, 35, 35), (14, 10 + bob), 1)
        elif direction == "right":
            pygame.draw.rect(surface, color, (23, 21 + bob, 8, 5))
            pygame.draw.circle(surface, (35, 35, 35), (22, 10 + bob), 1)
        elif direction == "up":
            pygame.draw.rect(surface, (70, 48, 35), (11, 5 + bob, 14, 8), border_radius=4)
        else:
            pygame.draw.circle(surface, (35, 35, 35), (15, 10 + bob), 1)
            pygame.draw.circle(surface, (35, 35, 35), (21, 10 + bob), 1)
        if state == "attack":
            if direction == "left":
                pygame.draw.line(surface, (230, 227, 202), (7, 19), (0, 17), 3)
            elif direction == "right":
                pygame.draw.line(surface, (230, 227, 202), (29, 19), (36, 17), 3)
            elif direction == "up":
                pygame.draw.line(surface, (230, 227, 202), (24, 18), (30, 7), 3)
            else:
                pygame.draw.line(surface, (230, 227, 202), (24, 25), (31, 35), 3)
        return surface
