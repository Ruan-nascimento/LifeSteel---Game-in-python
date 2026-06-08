from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

from src.core.settings import COLORS, Settings
from src.data.items_data import ITEMS
from src.systems.inventory_system import InventorySlot
from src.world.cave_generator import Cave, CaveEntrance, CaveGenerator
from src.world.chunk_manager import ChunkManager
from src.world.map_generator import MapGenerator
from src.world.resource_node import ResourceNode
from src.world.village_generator import Village, VillageGenerator


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
        return self.building_id in {"workbench", "campfire", "stone_stove", "small_chest", "chest"}

    def interface_kind(self) -> str | None:
        if self.building_id == "workbench":
            return "crafting"
        if self.building_id in {"campfire", "stone_stove"}:
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
        self.chunk_manager = ChunkManager(self, seed)
        self.villages: list[Village] = VillageGenerator(seed).generate_villages(self.width, self.height, self.spawn_tile)
        VillageGenerator(seed).apply_to_tiles(self.tiles, self.villages)
        self._clear_village_resources()
        self.cave_generator = CaveGenerator()
        self.cave_entrances: list[CaveEntrance] = self._generate_cave_entrances()
        self.caves: dict[str, Cave] = {}
        self.discovered_locations: set[str] = {"initial_clearing"}
        self.in_cave = False
        self.current_cave_id: str | None = None
        self._overworld_state: dict | None = None
        self._return_pos: pygame.Vector2 | None = None
        self.ruins = [
            pygame.Rect((self.spawn_tile[0] - 18) * Settings.TILE_SIZE, (self.spawn_tile[1] + 11) * Settings.TILE_SIZE, 96, 64),
            pygame.Rect((self.spawn_tile[0] + 32) * Settings.TILE_SIZE, (self.spawn_tile[1] + 22) * Settings.TILE_SIZE, 128, 64),
        ]

    def _generate_cave_entrances(self) -> list[CaveEntrance]:
        rng = random.Random(f"{self.seed}:caves")
        entrances: list[CaveEntrance] = []
        desired = 8
        attempts = 0
        while len(entrances) < desired and attempts < desired * 120:
            attempts += 1
            x = rng.randint(12, self.width - 13)
            y = rng.randint(12, self.height - 13)
            if self.tiles[y][x].kind == "water":
                continue
            if math.dist((x, y), self.spawn_tile) < 22:
                continue
            if any(math.dist((x, y), entrance.tile) < 20 for entrance in entrances):
                continue
            cave_id = f"cave_{x}_{y}_{len(entrances) + 1:02d}"
            difficulty = max(1, min(5, int(math.dist((x, y), self.spawn_tile) // 45) + 1))
            entrances.append(CaveEntrance(cave_id, (x, y), difficulty))
        return entrances

    def _clear_village_resources(self) -> None:
        if not self.villages:
            return
        kept = []
        for resource in self.resources:
            if any(abs(resource.tile_x - village.tile[0]) + abs(resource.tile_y - village.tile[1]) <= village.safe_radius_tiles + 2 for village in self.villages):
                continue
            kept.append(resource)
        self.resources = kept

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

    def collides(self, rect: pygame.Rect, allow_water: bool = False) -> bool:
        start_x = max(0, rect.left // Settings.TILE_SIZE)
        end_x = min(self.width - 1, rect.right // Settings.TILE_SIZE)
        start_y = max(0, rect.top // Settings.TILE_SIZE)
        end_y = min(self.height - 1, rect.bottom // Settings.TILE_SIZE)
        for ty in range(start_y, end_y + 1):
            for tx in range(start_x, end_x + 1):
                tile = self.tiles[ty][tx]
                if tile.solid and not (allow_water and tile.kind == "water") and rect.colliderect(pygame.Rect(tx * Settings.TILE_SIZE, ty * Settings.TILE_SIZE, Settings.TILE_SIZE, Settings.TILE_SIZE)):
                    return True
        for resource in self.resources:
            if resource.solid and rect.colliderect(resource.rect.inflate(-6, -6)):
                return True
        for structure in self.structures:
            if structure.building_id not in {"wood_floor"} and rect.colliderect(structure.rect.inflate(-4, -4)):
                return True
        return False

    def is_water_at(self, pos) -> bool:
        tx, ty = self.pixel_to_tile(pos)
        tile = self.tile_at(tx, ty)
        return bool(tile and tile.kind == "water")

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
            self.chunk_manager.mark_modified_at_tile(resource.tile_x, resource.tile_y)
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
        tx, ty = self.pixel_to_tile(pos)
        self.chunk_manager.mark_modified_at_tile(tx, ty)

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
        self.chunk_manager.mark_modified_at_tile(*tile)

    def _structure_state_to_dict(self, structure: Structure) -> dict | None:
        if structure.state is None:
            return None
        state = dict(structure.state)
        if "contents" in state:
            state["contents"] = [
                slot.to_dict() if slot else None
                for slot in state.get("contents") or []
            ]
        return state

    def _structure_state_from_dict(self, raw_state) -> dict | None:
        if raw_state is None:
            return None
        state = dict(raw_state)
        if "contents" in state:
            state["contents"] = [
                InventorySlot.from_dict(slot) if slot else None
                for slot in state.get("contents") or []
            ]
        return state

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

    def cave_entrance_near(self, player_center, range_px: int = 64) -> CaveEntrance | None:
        if self.in_cave:
            return None
        center = pygame.Vector2(player_center)
        matches = [entrance for entrance in self.cave_entrances if pygame.Vector2(entrance.rect.center).distance_to(center) <= range_px]
        return min(matches, key=lambda entrance: pygame.Vector2(entrance.rect.center).distance_to(center)) if matches else None

    def cave_exit_near(self, player_center, range_px: int = 64) -> bool:
        if not self.in_cave:
            return False
        exit_pos = pygame.Vector2((self.spawn_tile[0] + 0.5) * Settings.TILE_SIZE, (self.spawn_tile[1] + 0.5) * Settings.TILE_SIZE)
        return exit_pos.distance_to(player_center) <= range_px

    def enter_cave(self, entrance: CaveEntrance, player) -> None:
        if self.in_cave:
            return
        self._overworld_state = self._capture_active_state()
        self._return_pos = pygame.Vector2(player.center)
        cave = self.caves.get(entrance.cave_id)
        if cave is None:
            cave_seed = (self.seed * 131 + sum(ord(char) for char in entrance.cave_id)) % 10_000_000
            cave = self.cave_generator.generate_cave(entrance.cave_id, cave_seed, entrance.difficulty_level)
            self.caves[entrance.cave_id] = cave
        self._apply_cave(cave)
        self.in_cave = True
        self.current_cave_id = entrance.cave_id
        player.pos = self.spawn_pos.copy()
        self.discovered_locations.add(entrance.cave_id)

    def exit_cave(self, player) -> None:
        if not self.in_cave:
            return
        if self.current_cave_id and self.current_cave_id in self.caves:
            self._store_current_cave_state(self.caves[self.current_cave_id])
        return_pos = (self._return_pos or self.spawn_pos).copy()
        if self._overworld_state:
            self._restore_state(self._overworld_state)
        self.in_cave = False
        self.current_cave_id = None
        player.pos = return_pos
        self._return_pos = None

    def _apply_cave(self, cave: Cave) -> None:
        self.width = cave.width
        self.height = cave.height
        self.tiles = cave.tiles
        self.resources = cave.resources
        self.drops = cave.drops
        self.structures = cave.structures
        self.spawn_tile = cave.spawn_tile
        self.vendor_tile = cave.spawn_tile
        self.chunk_manager = ChunkManager(self, cave.seed)

    def _capture_active_state(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
            "tiles": self.tiles,
            "resources": self.resources,
            "drops": self.drops,
            "structures": self.structures,
            "spawn_tile": self.spawn_tile,
            "vendor_tile": self.vendor_tile,
            "chunk_manager": self.chunk_manager,
        }

    def _restore_state(self, state: dict) -> None:
        self.width = state["width"]
        self.height = state["height"]
        self.tiles = state["tiles"]
        self.resources = state["resources"]
        self.drops = state["drops"]
        self.structures = state["structures"]
        self.spawn_tile = state["spawn_tile"]
        self.vendor_tile = state["vendor_tile"]
        self.chunk_manager = state.get("chunk_manager") or ChunkManager(self, self.seed)

    def _store_current_cave_state(self, cave: Cave) -> None:
        cave.width = self.width
        cave.height = self.height
        cave.tiles = self.tiles
        cave.resources = self.resources
        cave.drops = self.drops
        cave.structures = self.structures
        cave.spawn_tile = self.spawn_tile
        cave.exit_tile = self.spawn_tile

    def update(self, dt: float, player_pos=None) -> None:
        if player_pos is not None:
            self.chunk_manager.update_active_chunks(pygame.Vector2(player_pos))
        for drop in self.drops:
            tx, ty = self.pixel_to_tile(drop.pos)
            if not self.chunk_manager.active_chunks or self.chunk_manager.is_active_tile(tx, ty):
                drop.age += dt

    def draw(self, surface: pygame.Surface, camera, exploration=None) -> None:
        tile_size = Settings.TILE_SIZE
        start_x, end_x, start_y, end_y = self.chunk_manager.tile_bounds_for_camera(camera)

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
        if not self.in_cave:
            for entrance in self.cave_entrances:
                if entrance.rect.colliderect(visible_rect):
                    drawables.append((entrance.rect.bottom, "cave_entrance", entrance))
            for village in self.villages:
                sign_rect = pygame.Rect(village.tile[0] * Settings.TILE_SIZE - 8, village.tile[1] * Settings.TILE_SIZE - 8, 48, 28)
                if sign_rect.colliderect(visible_rect):
                    drawables.append((sign_rect.bottom, "village_sign", village))
        elif self.current_cave_id:
            exit_rect = pygame.Rect(self.spawn_tile[0] * Settings.TILE_SIZE, self.spawn_tile[1] * Settings.TILE_SIZE, Settings.TILE_SIZE, Settings.TILE_SIZE)
            if exit_rect.colliderect(visible_rect):
                drawables.append((exit_rect.bottom, "cave_exit", exit_rect))
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
            elif kind == "cave_entrance":
                rect = camera.apply(obj.rect)
                pygame.draw.ellipse(surface, (16, 14, 17), rect.inflate(8, 4))
                pygame.draw.ellipse(surface, (72, 68, 72), rect.inflate(8, 4), 2)
            elif kind == "cave_exit":
                rect = camera.apply(obj)
                pygame.draw.rect(surface, (68, 58, 48), rect.inflate(4, 4), border_radius=4)
                pygame.draw.rect(surface, COLORS["accent"], rect.inflate(4, 4), 2, border_radius=4)
            elif kind == "village_sign":
                pos = pygame.Vector2(obj.tile[0] * Settings.TILE_SIZE, obj.tile[1] * Settings.TILE_SIZE) - camera.offset
                pygame.draw.rect(surface, (114, 75, 40), (pos.x - 8, pos.y - 8, 48, 24), border_radius=3)
                pygame.draw.rect(surface, (75, 47, 28), (pos.x - 8, pos.y - 8, 48, 24), 2, border_radius=3)
                font = pygame.font.SysFont(Settings.UI_FONT, 10, bold=True)
                label = font.render(obj.name.split()[0], True, COLORS["white"])
                surface.blit(label, (pos.x - 4, pos.y - 3))

        if exploration:
            fog = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
            fog.fill((*COLORS["fog"], 172))
            for ty in range(start_y, end_y):
                for tx in range(start_x, end_x):
                    if not exploration.is_explored(tx, ty):
                        surface.blit(fog, (tx * tile_size - camera.offset.x, ty * tile_size - camera.offset.y))

    def to_dict(self) -> dict:
        if self.in_cave and self.current_cave_id in self.caves:
            self._store_current_cave_state(self.caves[self.current_cave_id])
        overworld = self._overworld_state if self.in_cave and self._overworld_state else self._capture_active_state()
        resources = overworld["resources"]
        drops = overworld["drops"]
        structures = overworld["structures"]
        chunk_manager = overworld["chunk_manager"]
        return {
            "seed": self.seed,
            "map_width": Settings.WORLD_WIDTH,
            "map_height": Settings.WORLD_HEIGHT,
            "active_area": "cave" if self.in_cave else "overworld",
            "current_cave_id": self.current_cave_id,
            "return_pos": [self._return_pos.x, self._return_pos.y] if self._return_pos else None,
            "modified_chunks": chunk_manager.serialize_modified_chunks() if chunk_manager else {},
            "discovered_locations": sorted(self.discovered_locations),
            "villages": [village.to_dict() for village in self.villages],
            "cave_entrances": [entrance.to_dict() for entrance in self.cave_entrances],
            "caves": {
                cave_id: cave.to_dict(self._structure_state_to_dict)
                for cave_id, cave in self.caves.items()
            },
            "resources": [
                {"kind": r.kind, "tile_x": r.tile_x, "tile_y": r.tile_y, "hp": r.hp}
                for r in resources
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
                for d in drops
            ],
            "structures": [
                {"building_id": s.building_id, "tile": list(s.tile), "state": self._structure_state_to_dict(s)}
                for s in structures
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
            Structure(raw["building_id"], tuple(raw["tile"]), self._structure_state_from_dict(raw.get("state")))
            for raw in data.get("structures", [])
        ]
        self.chunk_manager = ChunkManager(self, self.seed)
        self.chunk_manager.deserialize_modified_chunks(data.get("modified_chunks", {}))
        if data.get("villages"):
            self.villages = [Village.from_dict(raw) for raw in data.get("villages", [])]
            VillageGenerator(self.seed).apply_to_tiles(self.tiles, self.villages)
            self._clear_village_resources()
        if data.get("cave_entrances"):
            self.cave_entrances = [CaveEntrance.from_dict(raw) for raw in data.get("cave_entrances", [])]
        self.discovered_locations = set(data.get("discovered_locations", ["initial_clearing"]))
        self.caves = {}
        for cave_id, raw in data.get("caves", {}).items():
            cave_seed = int(raw.get("seed", (self.seed * 131 + sum(ord(char) for char in cave_id)) % 10_000_000))
            cave = self.cave_generator.generate_cave(cave_id, cave_seed, int(raw.get("difficulty_level", 1)))
            cave.resources = []
            for res_raw in raw.get("resources", []):
                node = ResourceNode(res_raw["kind"], int(res_raw["tile_x"]), int(res_raw["tile_y"]))
                node.hp = int(res_raw.get("hp", node.hp))
                cave.resources.append(node)
            cave.drops = [
                GroundDrop(
                    drop_raw["item_id"],
                    int(drop_raw.get("quantity", 1)),
                    pygame.Vector2(drop_raw.get("pos", [0, 0])),
                    contents=[
                        InventorySlot.from_dict(slot) if slot else None
                        for slot in drop_raw.get("contents") or []
                    ] if drop_raw.get("contents") is not None else None,
                )
                for drop_raw in raw.get("drops", [])
            ]
            cave.structures = [
                Structure(struct_raw["building_id"], tuple(struct_raw["tile"]), self._structure_state_from_dict(struct_raw.get("state")))
                for struct_raw in raw.get("structures", [])
            ]
            self.caves[cave_id] = cave
        self.in_cave = False
        self.current_cave_id = None
        self._overworld_state = None
        self._return_pos = pygame.Vector2(data.get("return_pos")) if data.get("return_pos") else None
        current_cave_id = data.get("current_cave_id")
        if data.get("active_area") == "cave" and current_cave_id in self.caves:
            self._overworld_state = self._capture_active_state()
            self._apply_cave(self.caves[current_cave_id])
            self.in_cave = True
            self.current_cave_id = current_cave_id
