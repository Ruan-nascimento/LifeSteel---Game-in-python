from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from src.core.settings import COLORS, Settings
from src.data.items_data import ITEMS
from src.systems.inventory_system import InventorySlot
from src.world.map_generator import MapGenerator
from src.world.resource_node import ResourceNode


@dataclass
class GroundDrop:
    item_id: str
    quantity: int
    pos: pygame.Vector2
    age: float = 0.0
    contents: list[InventorySlot | None] | None = None

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.pos.x) - 10, int(self.pos.y) - 10, 20, 20)


@dataclass
class Structure:
    building_id: str
    tile: tuple[int, int]
    state: dict | None = None

    @property
    def rect(self) -> pygame.Rect:
        width = 64 if self.building_id == "small_shelter" else Settings.TILE_SIZE
        height = 64 if self.building_id == "small_shelter" else Settings.TILE_SIZE
        return pygame.Rect(self.tile[0] * Settings.TILE_SIZE, self.tile[1] * Settings.TILE_SIZE, width, height)

    def has_interface(self) -> bool:
        return self.building_id in {"workbench", "stone_stove", "small_chest", "chest"}

    def interface_kind(self) -> str | None:
        if self.building_id == "workbench":
            return "crafting"
        if self.building_id == "stone_stove":
            return "cooking"
        if self.building_id in {"small_chest", "chest"}:
            return "chest"
        return None

    def is_light_source(self, weather=None) -> bool:
        if self.building_id == "torch" and weather and weather.current in {"Chuvoso", "Tempestade"}:
            return False
        return self.building_id in {"torch", "campfire", "stone_stove"}

    def light_radius(self) -> int:
        if self.building_id == "campfire":
            return 145
        if self.building_id == "stone_stove":
            return 105
        return 96


class World:
    def __init__(self, asset_loader, seed: int = 1337) -> None:
        self.assets = asset_loader
        self.seed = seed
        self.width = Settings.WORLD_WIDTH
        self.height = Settings.WORLD_HEIGHT
        generator = MapGenerator(seed)
        self.tiles, self.resources, self.spawn_tile, self.vendor_tile = generator.generate()
        self.drops: list[GroundDrop] = []
        self.structures: list[Structure] = []
        self.ruins = [
            pygame.Rect((self.spawn_tile[0] - 18) * Settings.TILE_SIZE, (self.spawn_tile[1] + 11) * Settings.TILE_SIZE, 96, 64),
            pygame.Rect((self.spawn_tile[0] + 32) * Settings.TILE_SIZE, (self.spawn_tile[1] + 22) * Settings.TILE_SIZE, 128, 64),
        ]

    @property
    def pixel_width(self) -> int:
        return self.width * Settings.TILE_SIZE

    @property
    def pixel_height(self) -> int:
        return self.height * Settings.TILE_SIZE

    @property
    def spawn_pos(self) -> pygame.Vector2:
        return pygame.Vector2(
            self.spawn_tile[0] * Settings.TILE_SIZE + Settings.TILE_SIZE / 2,
            self.spawn_tile[1] * Settings.TILE_SIZE + Settings.TILE_SIZE / 2,
        )

    @property
    def vendor_pos(self) -> pygame.Vector2:
        return pygame.Vector2(
            self.vendor_tile[0] * Settings.TILE_SIZE + Settings.TILE_SIZE / 2,
            self.vendor_tile[1] * Settings.TILE_SIZE + Settings.TILE_SIZE / 2,
        )

    def pixel_to_tile(self, pos) -> tuple[int, int]:
        return (int(pos[0] // Settings.TILE_SIZE), int(pos[1] // Settings.TILE_SIZE))

    def tile_at(self, tx: int, ty: int):
        if 0 <= tx < self.width and 0 <= ty < self.height:
            return self.tiles[ty][tx]
        return None

    def collides(self, rect: pygame.Rect) -> bool:
        start_x = max(0, rect.left // Settings.TILE_SIZE)
        end_x = min(self.width - 1, rect.right // Settings.TILE_SIZE)
        start_y = max(0, rect.top // Settings.TILE_SIZE)
        end_y = min(self.height - 1, rect.bottom // Settings.TILE_SIZE)
        for ty in range(start_y, end_y + 1):
            for tx in range(start_x, end_x + 1):
                tile = self.tiles[ty][tx]
                if tile.solid and rect.colliderect(pygame.Rect(tx * Settings.TILE_SIZE, ty * Settings.TILE_SIZE, Settings.TILE_SIZE, Settings.TILE_SIZE)):
                    return True
        for resource in self.resources:
            if resource.solid and rect.colliderect(resource.rect.inflate(-6, -6)):
                return True
        for structure in self.structures:
            if structure.building_id not in {"wood_floor"} and rect.colliderect(structure.rect.inflate(-4, -4)):
                return True
        return False

    def is_water_near(self, pos, distance_px: int = 48) -> bool:
        center = pygame.Vector2(pos)
        tx, ty = self.pixel_to_tile(center)
        radius = max(1, distance_px // Settings.TILE_SIZE)
        for y in range(ty - radius, ty + radius + 1):
            for x in range(tx - radius, tx + radius + 1):
                tile = self.tile_at(x, y)
                if tile and tile.kind == "water":
                    tile_center = pygame.Vector2((x + 0.5) * Settings.TILE_SIZE, (y + 0.5) * Settings.TILE_SIZE)
                    if tile_center.distance_to(center) <= distance_px:
                        return True
        return False

    def resource_near_point(self, point, range_px: int, player_center) -> ResourceNode | None:
        point = pygame.Vector2(point)
        player_center = pygame.Vector2(player_center)
        candidates = []
        for resource in self.resources:
            if resource.center.distance_to(player_center) <= range_px + 16:
                if resource.rect.inflate(20, 20).collidepoint(point):
                    candidates.append(resource)
        if candidates:
            return min(candidates, key=lambda node: node.center.distance_to(point))
        nearby = [node for node in self.resources if node.center.distance_to(player_center) <= min(range_px, Settings.INTERACTION_RANGE)]
        if nearby:
            return min(nearby, key=lambda node: node.center.distance_to(player_center))
        return None

    def remove_resource(self, resource: ResourceNode) -> None:
        if resource in self.resources:
            self.resources.remove(resource)

    def spawn_ground_drop(self, pos, item_id: str, quantity: int, contents: list[InventorySlot | None] | None = None) -> None:
        if quantity <= 0:
            return
        offset = pygame.Vector2(math.sin(len(self.drops)) * 12, math.cos(len(self.drops)) * 12)
        cloned_contents = [
            slot.clone() if slot else None
            for slot in contents
        ] if contents is not None else None
        self.drops.append(GroundDrop(item_id, quantity, pygame.Vector2(pos) + offset, contents=cloned_contents))

    def spawn_floating_drop(self, pos, item_id: str, quantity: int) -> None:
        self.spawn_ground_drop(pos, item_id, quantity)

    def pick_drops_near(self, pos, radius: int = 42) -> list[GroundDrop]:
        picked: list[GroundDrop] = []
        center = pygame.Vector2(pos)
        remaining: list[GroundDrop] = []
        for drop in self.drops:
            if drop.pos.distance_to(center) <= radius:
                picked.append(drop)
            else:
                remaining.append(drop)
        self.drops = remaining
        return picked

    def item_name(self, item_id: str) -> str:
        return ITEMS.get(item_id, {}).get("name", item_id)

    def can_place_structure(self, tile: tuple[int, int]) -> bool:
        tx, ty = tile
        if not (0 <= tx < self.width and 0 <= ty < self.height):
            return False
        if self.tiles[ty][tx].kind == "water":
            return False
        rect = pygame.Rect(tx * Settings.TILE_SIZE, ty * Settings.TILE_SIZE, Settings.TILE_SIZE, Settings.TILE_SIZE)
        if any(resource.rect.colliderect(rect) for resource in self.resources):
            return False
        if any(structure.rect.colliderect(rect) for structure in self.structures):
            return False
        return True

    def add_structure(self, building_id: str, tile: tuple[int, int]) -> None:
        state = {}
        if building_id in {"small_chest", "chest"}:
            state["contents"] = [None for _ in range(12)]
        self.structures.append(Structure(building_id, tile, state))

    def structure_at_point(self, point, player_center=None, range_px: int = 72) -> Structure | None:
        point = pygame.Vector2(point)
        matches = []
        for structure in self.structures:
            if structure.rect.inflate(8, 8).collidepoint(point):
                if player_center is None or pygame.Vector2(structure.rect.center).distance_to(player_center) <= range_px:
                    matches.append(structure)
        if not matches:
            return None
        return min(matches, key=lambda structure: pygame.Vector2(structure.rect.center).distance_to(point))

    def nearby_structure_with_interface(self, player_center, range_px: int = 64) -> Structure | None:
        center = pygame.Vector2(player_center)
        matches = [
            structure
            for structure in self.structures
            if structure.has_interface() and pygame.Vector2(structure.rect.center).distance_to(center) <= range_px
        ]
        return min(matches, key=lambda structure: pygame.Vector2(structure.rect.center).distance_to(center)) if matches else None

    def light_sources(self, weather) -> list[tuple[pygame.Vector2, int, tuple[int, int, int]]]:
        result = []
        for structure in self.structures:
            if structure.is_light_source(weather):
                color = (255, 174, 72) if structure.building_id != "stone_stove" else (255, 125, 67)
                result.append((pygame.Vector2(structure.rect.center), structure.light_radius(), color))
        return result

    def update(self, dt: float) -> None:
        for drop in self.drops:
            drop.age += dt

    def draw(self, surface: pygame.Surface, camera, exploration=None) -> None:
        tile_size = Settings.TILE_SIZE
        start_x = max(0, int(camera.offset.x // tile_size) - 1)
        end_x = min(self.width, int((camera.offset.x + camera.screen_width) // tile_size) + 2)
        start_y = max(0, int(camera.offset.y // tile_size) - 1)
        end_y = min(self.height, int((camera.offset.y + camera.screen_height) // tile_size) + 2)

        for ty in range(start_y, end_y):
            for tx in range(start_x, end_x):
                tile = self.tiles[ty][tx]
                image = self.assets.tiles.get(tile.kind, self.assets.tiles["grass"])
                surface.blit(image, (tx * tile_size - camera.offset.x, ty * tile_size - camera.offset.y))

        for ruin in self.ruins:
            if ruin.colliderect(pygame.Rect(camera.offset.x, camera.offset.y, camera.screen_width, camera.screen_height)):
                screen_rect = camera.apply(ruin)
                pygame.draw.rect(surface, (87, 87, 78), screen_rect, border_radius=2)
                pygame.draw.rect(surface, (50, 52, 49), screen_rect, 2, border_radius=2)
                pygame.draw.line(surface, (126, 126, 112), screen_rect.topleft, screen_rect.bottomright, 2)

        visible_rect = pygame.Rect(camera.offset.x - 64, camera.offset.y - 64, camera.screen_width + 128, camera.screen_height + 128)
        drawables = []
        for resource in self.resources:
            if resource.rect.colliderect(visible_rect):
                drawables.append((resource.rect.bottom, "resource", resource))
        for structure in self.structures:
            if structure.rect.colliderect(visible_rect):
                drawables.append((structure.rect.bottom, "structure", structure))
        for drop in self.drops:
            if drop.rect.colliderect(visible_rect):
                drawables.append((drop.rect.bottom, "drop", drop))
        drawables.sort(key=lambda item: item[0])

        for _, kind, obj in drawables:
            if kind == "resource":
                image = self.assets.resources[obj.kind]
                pos = pygame.Vector2(obj.rect.topleft) - camera.offset
                if obj.kind == "tree":
                    pos.y -= 18
                surface.blit(image, pos)
            elif kind == "structure":
                image = self.assets.buildings.get(obj.building_id.replace("small_", "").replace("simple_", ""), None)
                if obj.building_id == "campfire":
                    image = self.assets.buildings["campfire"]
                elif obj.building_id == "small_chest":
                    image = self.assets.buildings["chest"]
                elif obj.building_id == "workbench":
                    image = self.assets.buildings["workbench"]
                elif obj.building_id == "small_shelter":
                    image = self.assets.buildings["shelter"]
                elif obj.building_id == "simple_bed":
                    image = self.assets.buildings["bed"]
                elif obj.building_id == "simple_wall":
                    image = self.assets.buildings["wall"]
                elif obj.building_id == "wood_floor":
                    image = self.assets.buildings["wood_floor"]
                elif obj.building_id == "torch":
                    image = self.assets.buildings["torch"]
                elif obj.building_id == "fence":
                    image = self.assets.buildings["fence"]
                elif obj.building_id == "stone_stove":
                    image = self.assets.buildings["stone_stove"]
                surface.blit(image, pygame.Vector2(obj.rect.topleft) - camera.offset)
            elif kind == "drop":
                bob = math.sin(obj.age * 6) * 3
                icon = self.assets.item_icon(obj.item_id, 22)
                surface.blit(icon, obj.pos - camera.offset + pygame.Vector2(-11, -13 + bob))
                if obj.quantity > 1:
                    font = pygame.font.SysFont(Settings.UI_FONT, 12)
                    label = font.render(str(obj.quantity), True, COLORS["white"])
                    surface.blit(label, obj.pos - camera.offset + pygame.Vector2(3, -2 + bob))

        if exploration:
            fog = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
            fog.fill((*COLORS["fog"], 172))
            for ty in range(start_y, end_y):
                for tx in range(start_x, end_x):
                    if not exploration.is_explored(tx, ty):
                        surface.blit(fog, (tx * tile_size - camera.offset.x, ty * tile_size - camera.offset.y))

    def to_dict(self) -> dict:
        return {
            "seed": self.seed,
            "resources": [
                {"kind": r.kind, "tile_x": r.tile_x, "tile_y": r.tile_y, "hp": r.hp}
                for r in self.resources
            ],
            "drops": [
                {
                    "item_id": d.item_id,
                    "quantity": d.quantity,
                    "pos": [d.pos.x, d.pos.y],
                    "contents": [
                        slot.to_dict() if slot else None
                        for slot in d.contents
                    ] if d.contents is not None else None,
                }
                for d in self.drops
            ],
            "structures": [
                {"building_id": s.building_id, "tile": list(s.tile), "state": s.state}
                for s in self.structures
            ],
        }

    def load_dict(self, data: dict) -> None:
        self.seed = int(data.get("seed", self.seed))
        self.resources = []
        for raw in data.get("resources", []):
            node = ResourceNode(raw["kind"], int(raw["tile_x"]), int(raw["tile_y"]))
            node.hp = int(raw.get("hp", node.hp))
            self.resources.append(node)
        self.drops = [
            GroundDrop(
                raw["item_id"],
                int(raw.get("quantity", 1)),
                pygame.Vector2(raw.get("pos", [0, 0])),
                contents=[
                    InventorySlot.from_dict(slot) if slot else None
                    for slot in raw.get("contents") or []
                ] if raw.get("contents") is not None else None,
            )
            for raw in data.get("drops", [])
        ]
        self.structures = [
            Structure(raw["building_id"], tuple(raw["tile"]), raw.get("state"))
            for raw in data.get("structures", [])
        ]
