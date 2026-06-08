from __future__ import annotations

from src.core.settings import Settings


class WaterSystem:
    def __init__(self) -> None:
        self.drowning_timer = 0.0
        self.drowning_step = 0
        self.message = ""
        self.player_in_water = False

    def update(self, dt: float, player, world) -> list[str]:
        messages: list[str] = []
        in_water = bool(world and hasattr(world, "is_water_at") and world.is_water_at(player.center))
        self.player_in_water = in_water
        if not in_water:
            self.drowning_timer = 0.0
            self.drowning_step = 0
            if "Nadando" in player.status_effects:
                player.status_effects.remove("Nadando")
            return messages

        player.energy = max(0.0, player.energy - Settings.WATER_ENERGY_DRAIN_PER_SECOND * dt)
        if "Nadando" not in player.status_effects:
            player.status_effects.append("Nadando")
        if player.energy > 0:
            self.drowning_timer = 0.0
            self.drowning_step = 0
            return messages

        self.drowning_timer += dt
        if self.drowning_timer >= Settings.WATER_DAMAGE_INTERVAL:
            self.drowning_timer = 0.0
            self.drowning_step += 1
            percent = min(
                Settings.WATER_MAX_DAMAGE_PERCENT,
                Settings.WATER_MIN_DAMAGE_PERCENT + (self.drowning_step - 1) * Settings.WATER_DAMAGE_ESCALATION_PERCENT,
            )
            damage = max(1, int(player.max_hp * percent))
            player.take_damage(damage)
            self.message = f"Voce esta se afogando: -{damage} HP."
            messages.append(self.message)
        return messages

    def to_dict(self) -> dict:
        return {"drowning_timer": self.drowning_timer, "drowning_step": self.drowning_step}

    @classmethod
    def from_dict(cls, data: dict | None) -> "WaterSystem":
        system = cls()
        if data:
            system.drowning_timer = float(data.get("drowning_timer", 0))
            system.drowning_step = int(data.get("drowning_step", 0))
        return system
