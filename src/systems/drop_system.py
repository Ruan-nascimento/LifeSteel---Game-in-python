from __future__ import annotations

import random

from src.data.food_data import drop_sources, source_terms


RARITY_DROP_MULTIPLIER = {
    "common": 1.0,
    "uncommon": 0.9,
    "rare": 0.75,
    "epic": 0.55,
    "legendary": 0.35,
}


class DropSystem:
    def __init__(self, rng=None) -> None:
        self.rng = rng or random.Random()
        self.sources = drop_sources()

    def roll_drop(self, source_id: str, luck: float = 0.0) -> dict[str, int]:
        drops: dict[str, int] = {}
        for term in source_terms(source_id):
            for rule in self.sources.get(term, []):
                item_id = rule["item_id"]
                chance = float(rule.get("drop_chance", 0))
                rarity = str(rule.get("rarity", "common"))
                chance *= RARITY_DROP_MULTIPLIER.get(rarity, 1.0)
                chance += max(0.0, luck) * 0.01
                if self.rng.random() > min(1.0, chance):
                    continue
                minimum = int(rule.get("min_quantity", 1))
                maximum = max(minimum, int(rule.get("max_quantity", minimum)))
                drops[item_id] = drops.get(item_id, 0) + self.rng.randint(minimum, maximum)
        return drops

    def controlled_item_ids(self, source_id: str) -> set[str]:
        item_ids: set[str] = set()
        for term in source_terms(source_id):
            for rule in self.sources.get(term, []):
                item_ids.add(rule["item_id"])
        return item_ids
