from __future__ import annotations

import random
from dataclasses import dataclass

import pygame

from src.core.json_loader import load_json
from src.core.settings import BASE_DIR, Settings
from src.entities.enemy import Enemy


MOBS_PATH = BASE_DIR / "src" / "data" / "mobs.json"


@dataclass(frozen=True)
class MobSpawnRule:
    mob_id: str
    name: str
    level: int
    rarity: str
    spawn_phases: tuple[str, ...]
    biomes: tuple[str, ...]
    max_per_chunk: int

    @classmethod
    def from_dict(cls, data: dict) -> "MobSpawnRule":
        return cls(
            mob_id=data["id"],
            name=data.get("name", data["id"]),
            level=int(data.get("level", 1)),
            rarity=data.get("rarity", "common"),
            spawn_phases=tuple(data.get("spawn_phases", [])),
            biomes=tuple(data.get("biomes", [])),
            max_per_chunk=int(data.get("max_per_chunk", Settings.MAX_MOBS_PER_CHUNK)),
        )


class MobSpawnSystem:
    def __init__(self, world=None, player=None, time_system=None, data_path=MOBS_PATH) -> None:
        self.world = world
        self.player = player
        self.time_system = time_system
        data = load_json(data_path, {"mobs": []})
        self.rules = [MobSpawnRule.from_dict(entry) for entry in data.get("mobs", [])]
        self._rng = random.Random(getattr(world, "seed", 1337))
        self.spawn_timer = self._next_interval()

    def bind(self, world, player, time_system) -> None:
        self.world = world
        self.player = player
        self.time_system = time_system
        self._rng.seed(getattr(world, "seed", 1337))

    def update(self, dt: float, enemies: list[Enemy], asset_loader) -> list[Enemy]:
        if not self.world or not self.player or not self.time_system:
            return []
        self.spawn_timer -= dt
        if self.spawn_timer > 0:
            return []
        self.spawn_timer = self._next_interval()
        spawned = self.try_spawn_near_player(enemies, asset_loader)
        return [spawned] if spawned else []

    def try_spawn_near_player(self, enemies: list[Enemy], asset_loader) -> Enemy | None:
        active = [enemy for enemy in enemies if enemy.alive]
        max_active = 25 if Settings.LOW_PERFORMANCE_MODE else Settings.MAX_ACTIVE_MOBS
        if len(active) >= max_active:
            return None
        player_chunk = self.world.chunk_manager.get_chunk_coords_from_world_pos(self.player.center.x, self.player.center.y)
        candidate_chunks = self.world.chunk_manager.get_nearby_chunks(player_chunk[0], player_chunk[1], Settings.ACTIVE_CHUNK_RADIUS)
        self._rng.shuffle(candidate_chunks)
        phase = self.time_system.get_day_phase()
        for chunk in candidate_chunks:
            if self._mobs_in_chunk(active, chunk.chunk_x, chunk.chunk_y) >= Settings.MAX_MOBS_PER_CHUNK:
                continue
            rule = self.choose_mob_for_context(chunk.biome, phase, self.player.level.level)
            if not rule or self._mobs_in_chunk(active, chunk.chunk_x, chunk.chunk_y, rule.mob_id) >= rule.max_per_chunk:
                continue
            pos = self.get_valid_spawn_position(chunk)
            if pos is None:
                continue
            enemy = Enemy(rule.mob_id, pos, asset_loader, base_level=max(1, min(5, rule.level)))
            return enemy
        return None

    def get_valid_spawn_position(self, chunk) -> pygame.Vector2 | None:
        tile_min_x = chunk.chunk_x * Settings.CHUNK_SIZE
        tile_min_y = chunk.chunk_y * Settings.CHUNK_SIZE
        for _ in range(24):
            tx = self._rng.randint(tile_min_x, min(self.world.width - 2, tile_min_x + Settings.CHUNK_SIZE - 1))
            ty = self._rng.randint(tile_min_y, min(self.world.height - 2, tile_min_y + Settings.CHUNK_SIZE - 1))
            pos = pygame.Vector2((tx + 0.5) * Settings.TILE_SIZE, (ty + 0.5) * Settings.TILE_SIZE)
            if self.can_spawn_at(pos.x, pos.y):
                return pos
        return None

    def choose_mob_for_context(self, biome: str, day_phase: str, player_level: int) -> MobSpawnRule | None:
        max_level = player_level + (2 if day_phase == "night" else 1)
        candidates = [
            rule
            for rule in self.rules
            if day_phase in rule.spawn_phases
            and rule.level <= max_level
            and (biome in rule.biomes or ("cave" in rule.biomes and getattr(self.world, "in_cave", False)))
        ]
        if not candidates:
            return None
        weights = []
        for rule in candidates:
            rarity_weight = {"common": 6, "uncommon": 3, "rare": 1.4, "epic": 0.55}.get(rule.rarity, 2)
            level_weight = max(0.5, 2.5 - max(0, rule.level - player_level) * 0.6)
            if day_phase == "night" and rule.level >= player_level:
                level_weight += 0.8
            weights.append(rarity_weight * level_weight)
        return self._rng.choices(candidates, weights=weights, k=1)[0]

    def can_spawn_at(self, world_x, world_y) -> bool:
        pos = pygame.Vector2(world_x, world_y)
        distance = pos.distance_to(self.player.center)
        if distance < Settings.MIN_SPAWN_DISTANCE_FROM_PLAYER or distance > Settings.MAX_SPAWN_DISTANCE_FROM_PLAYER:
            return False
        if getattr(self.world, "is_water_at", None) and self.world.is_water_at(pos):
            return False
        rect = pygame.Rect(world_x - 14, world_y - 14, 28, 28)
        if self.world.collides(rect):
            return False
        if not getattr(self.world, "in_cave", False):
            for village in getattr(self.world, "villages", []):
                if village.rect.collidepoint(pos):
                    return False
        return True

    def _mobs_in_chunk(self, enemies: list[Enemy], chunk_x: int, chunk_y: int, mob_id: str | None = None) -> int:
        count = 0
        for enemy in enemies:
            if mob_id and enemy.kind != mob_id:
                continue
            ex, ey = self.world.chunk_manager.get_chunk_coords_from_world_pos(enemy.center.x, enemy.center.y)
            if (ex, ey) == (chunk_x, chunk_y):
                count += 1
        return count

    def _next_interval(self) -> float:
        return self._rng.uniform(Settings.MOB_SPAWN_INTERVAL_MIN, Settings.MOB_SPAWN_INTERVAL_MAX)

    def to_dict(self) -> dict:
        return {"spawn_timer": self.spawn_timer}

    @classmethod
    def from_dict(cls, data: dict | None, world=None, player=None, time_system=None) -> "MobSpawnSystem":
        system = cls(world, player, time_system)
        if data:
            system.spawn_timer = float(data.get("spawn_timer", system.spawn_timer))
        return system
