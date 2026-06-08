from __future__ import annotations

from src.core.json_loader import load_json
from src.core.settings import BASE_DIR


LEVEL_GROWTH_PATH = BASE_DIR / "src" / "data" / "level_growth.json"


class LevelGrowthSystem:
    def __init__(self, data_path=LEVEL_GROWTH_PATH) -> None:
        self.data = load_json(data_path, {"growth_by_class": {}})

    def apply_pending_growth(self, player) -> list[str]:
        applied = int(getattr(player, "growth_level_applied", 1))
        current = int(player.level.level)
        if current <= applied:
            return []
        messages: list[str] = []
        growth = self.data.get("growth_by_class", {}).get(player.class_id, {})
        for level in range(applied + 1, current + 1):
            hp_gain = int(growth.get("health", 12))
            mana_gain = int(growth.get("mana", 6))
            energy_gain = int(growth.get("energy", 8))
            hunger_gain = int(growth.get("hunger", 4))
            thirst_gain = int(growth.get("thirst", 4))
            player.max_hp += hp_gain
            player.max_mana += mana_gain
            player.max_energy += energy_gain
            player.max_hunger += hunger_gain
            player.max_thirst += thirst_gain
            player.hp = min(player.max_hp, player.hp + max(1, int(player.max_hp * float(self.data.get("heal_on_level_up_percent", 0.5)))))
            player.mana = min(player.max_mana, player.mana + max(1, int(player.max_mana * float(self.data.get("restore_mana_on_level_up_percent", 0.5)))))
            player.energy = min(player.max_energy, player.energy + max(1, int(player.max_energy * float(self.data.get("restore_energy_on_level_up_percent", 0.5)))))
            messages.append(f"Level {level}: atributos maximos aumentaram.")
        player.growth_level_applied = current
        return messages
