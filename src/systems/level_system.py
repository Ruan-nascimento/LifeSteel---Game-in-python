class LevelSystem:
    THRESHOLDS = [50, 120, 250, 450, 750, 1120, 1600, 2200, 2950, 3850]

    def __init__(self, level: int = 1, xp: int = 0) -> None:
        self.level = level
        self.xp = xp

    @property
    def next_total_xp(self) -> int:
        if self.level - 1 < len(self.THRESHOLDS):
            return self.THRESHOLDS[self.level - 1]
        return self.THRESHOLDS[-1] + (self.level - len(self.THRESHOLDS)) * 1200

    @property
    def previous_total_xp(self) -> int:
        if self.level <= 1:
            return 0
        if self.level - 2 < len(self.THRESHOLDS):
            return self.THRESHOLDS[self.level - 2]
        return self.THRESHOLDS[-1] + (self.level - len(self.THRESHOLDS) - 1) * 1200

    @property
    def current_level_xp(self) -> int:
        return max(0, self.xp - self.previous_total_xp)

    @property
    def xp_needed_this_level(self) -> int:
        return max(1, self.next_total_xp - self.previous_total_xp)

    def add_xp(self, amount: int) -> list[int]:
        if amount <= 0:
            return []
        self.xp += amount
        level_ups: list[int] = []
        while self.xp >= self.next_total_xp:
            self.level += 1
            level_ups.append(self.level)
        return level_ups

    def to_dict(self) -> dict:
        return {"level": self.level, "xp": self.xp}

    @classmethod
    def from_dict(cls, data: dict) -> "LevelSystem":
        return cls(level=int(data.get("level", 1)), xp=int(data.get("xp", 0)))
