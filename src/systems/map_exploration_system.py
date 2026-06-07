from __future__ import annotations

from src.core.settings import Settings


class MapExplorationSystem:
    def __init__(self, world) -> None:
        self.world = world
        self.explored: set[tuple[int, int]] = set()

    def reveal_around(self, pos, radius_px: int) -> None:
        tile_size = Settings.TILE_SIZE
        center_x = int(pos.x // tile_size)
        center_y = int(pos.y // tile_size)
        radius_tiles = max(2, int(radius_px // tile_size))
        for ty in range(center_y - radius_tiles, center_y + radius_tiles + 1):
            for tx in range(center_x - radius_tiles, center_x + radius_tiles + 1):
                if 0 <= tx < self.world.width and 0 <= ty < self.world.height:
                    if (tx - center_x) ** 2 + (ty - center_y) ** 2 <= radius_tiles ** 2:
                        self.explored.add((tx, ty))

    def is_explored(self, tx: int, ty: int) -> bool:
        return (tx, ty) in self.explored

    def to_list(self) -> list[list[int]]:
        return [[x, y] for x, y in sorted(self.explored)]

    def from_list(self, data: list[list[int]]) -> None:
        self.explored = {(int(x), int(y)) for x, y in data}
