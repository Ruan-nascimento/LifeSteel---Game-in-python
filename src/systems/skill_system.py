from __future__ import annotations

from dataclasses import dataclass

from src.data.skills_data import SKILL_NAMES


@dataclass
class Skill:
    name: str
    level: int = 1
    xp: int = 0

    @property
    def xp_to_next(self) -> int:
        return int(50 * (1.35 ** (self.level - 1)))

    def add_xp(self, amount: int) -> bool:
        if amount <= 0:
            return False
        self.xp += amount
        leveled = False
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            leveled = True
        return leveled

    def to_dict(self) -> dict:
        return {"name": self.name, "level": self.level, "xp": self.xp}


class SkillTree:
    def __init__(self) -> None:
        self.skills = {name: Skill(name) for name in SKILL_NAMES}

    def apply_class_affinity(self, skill_names: list[str]) -> None:
        for name in skill_names:
            if name in self.skills:
                self.skills[name].xp = 20

    def add_xp(self, name: str, amount: int) -> bool:
        if name not in self.skills:
            self.skills[name] = Skill(name)
        return self.skills[name].add_xp(amount)

    def level(self, name: str) -> int:
        return self.skills.get(name, Skill(name)).level

    def communication_discount(self) -> float:
        return min(0.25, (self.level("Comunicacao") - 1) * 0.04)

    def commerce_sell_bonus(self) -> float:
        return min(0.30, (self.level("Comercio") - 1) * 0.05 + (self.level("Politica") - 1) * 0.02)

    def exploration_radius_bonus(self) -> int:
        return (self.level("Exploracao") - 1) * 18

    def building_cost_discount(self) -> float:
        return min(0.20, (self.level("Construcao") - 1) * 0.035)

    def to_dict(self) -> dict:
        return {name: skill.to_dict() for name, skill in self.skills.items()}

    @classmethod
    def from_dict(cls, data: dict) -> "SkillTree":
        tree = cls()
        for name, raw in data.items():
            tree.skills[name] = Skill(
                name=name,
                level=int(raw.get("level", 1)),
                xp=int(raw.get("xp", 0)),
            )
        return tree
