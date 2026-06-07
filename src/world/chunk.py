from dataclasses import dataclass, field

from src.core.settings import Settings


@dataclass
class Chunk:
    chunk_x: int
    chunk_y: int
    resources: list = field(default_factory=list)

    @property
    def rect_tiles(self) -> tuple[int, int, int, int]:
        size = Settings.CHUNK_SIZE
        return (self.chunk_x * size, self.chunk_y * size, size, size)
