from dataclasses import dataclass


@dataclass(frozen=True)
class Biome:
    name: str
    primary_tile: str
    tree_density: float
    stone_density: float
    enemy_density: float


FOREST_BIOME = Biome(
    name="Floresta Inicial",
    primary_tile="grass",
    tree_density=0.12,
    stone_density=0.04,
    enemy_density=0.02,
)
