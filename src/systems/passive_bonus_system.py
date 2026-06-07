from __future__ import annotations


class PassiveBonusSystem:
    def __init__(self) -> None:
        self.message = "Bonus passivos prontos."

    def apply_bonus(self, player, bonus: dict, source_id: str | None = None) -> bool:
        if not bonus:
            self.message = "Nenhum bonus para aplicar."
            return False
        applied_sources = getattr(player, "passive_bonus_sources", set())
        if source_id and source_id in applied_sources:
            self.message = "Bonus ja aplicado anteriormente."
            return False
        if not hasattr(player, "passive_bonuses"):
            player.passive_bonuses = {}
        for key, value in bonus.items():
            if isinstance(value, (int, float)):
                player.passive_bonuses[key] = player.passive_bonuses.get(key, 0) + value
            else:
                player.passive_bonuses[key] = value
        if source_id:
            applied_sources.add(source_id)
            player.passive_bonus_sources = applied_sources
        self.message = "Bonus passivo aplicado."
        return True

    def value(self, player, key: str, default: int | float = 0):
        return getattr(player, "passive_bonuses", {}).get(key, default)

    def to_dict(self, player) -> dict:
        return dict(getattr(player, "passive_bonuses", {}))
