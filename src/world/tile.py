from dataclasses import dataclass


@dataclass
class Tile:
    x: int
    y: int
    kind: str

    @property
    def solid(self) -> bool:
        return self.kind == "water"
