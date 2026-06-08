from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Biome:
    biome_id: str
    tile_weights: dict[str, float]
    tree_density: float
    stone_density: float
    ore_density: float
    bush_density: float
    water_bias: float = 0.0


BIOMES = {
    "forest": Biome("forest", {"grass": 0.65, "grass_dark": 0.2, "grass_light": 0.1, "soil": 0.05}, 0.08, 0.018, 0.006, 0.035),
    "dense_forest": Biome("dense_forest", {"grass_dark": 0.58, "grass": 0.28, "grass_light": 0.05, "soil": 0.09}, 0.14, 0.012, 0.004, 0.055),
    "clearing": Biome("clearing", {"grass_light": 0.42, "grass": 0.48, "path": 0.03, "soil": 0.07}, 0.025, 0.008, 0.002, 0.02),
    "lake": Biome("lake", {"water": 0.42, "grass": 0.28, "soil": 0.2, "grass_light": 0.1}, 0.025, 0.01, 0.002, 0.025, 0.35),
    "rocky": Biome("rocky", {"grass": 0.35, "soil": 0.25, "grass_dark": 0.12, "path": 0.08, "grass_light": 0.2}, 0.018, 0.09, 0.045, 0.012),
    "swamp": Biome("swamp", {"grass_dark": 0.38, "water": 0.24, "soil": 0.22, "grass": 0.16}, 0.06, 0.012, 0.005, 0.045, 0.2),
    "field": Biome("field", {"grass_light": 0.55, "grass": 0.34, "soil": 0.08, "path": 0.03}, 0.018, 0.012, 0.002, 0.018),
    "village_region": Biome("village_region", {"grass": 0.42, "grass_light": 0.26, "path": 0.22, "soil": 0.1}, 0.01, 0.006, 0.001, 0.01),
    "cave": Biome("cave", {"soil": 0.42, "path": 0.26, "grass_dark": 0.2, "water": 0.12}, 0.0, 0.12, 0.08, 0.025),
}


def biome_for_chunk(seed: int, chunk_x: int, chunk_y: int) -> str:
    value = abs((chunk_x * 928371 + chunk_y * 689287 + seed * 31) % 100)
    if value < 10:
        return "lake"
    if value < 22:
        return "rocky"
    if value < 32:
        return "field"
    if value < 42:
        return "swamp"
    if value < 62:
        return "dense_forest"
    return "forest"
