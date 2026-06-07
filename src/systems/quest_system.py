from __future__ import annotations

from dataclasses import dataclass, field

from src.data.quests_data import QUESTS


@dataclass
class QuestProgress:
    quest_id: str
    active: bool = True
    completed: bool = False
    counters: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "quest_id": self.quest_id,
            "active": self.active,
            "completed": self.completed,
            "counters": self.counters,
        }


class QuestSystem:
    def __init__(self) -> None:
        self.quests = {"first_shelter": QuestProgress("first_shelter")}
        self.message = "Missao inicial: Primeiro Abrigo."

    def register_collect(self, item_id: str, amount: int = 1) -> None:
        for progress in self.quests.values():
            if progress.completed:
                continue
            key = f"collect:{item_id}"
            progress.counters[key] = progress.counters.get(key, 0) + amount

    def register_build(self, building_id: str, amount: int = 1) -> None:
        for progress in self.quests.values():
            if progress.completed:
                continue
            key = f"build:{building_id}"
            progress.counters[key] = progress.counters.get(key, 0) + amount

    def update_completion(self, player) -> list[str]:
        completed = []
        for quest_id, progress in self.quests.items():
            if progress.completed:
                continue
            quest = QUESTS[quest_id]
            done = True
            for objective in quest["objectives"]:
                key = f"{objective['type']}:{objective.get('item') or objective.get('building')}"
                if progress.counters.get(key, 0) < objective["amount"]:
                    done = False
                    break
            if done:
                self._grant_rewards(player, quest_id)
                progress.completed = True
                progress.active = False
                completed.append(quest_id)
        return completed

    def _grant_rewards(self, player, quest_id: str) -> None:
        rewards = QUESTS[quest_id]["rewards"]
        player.level.add_xp(int(rewards.get("xp", 0)))
        player.coins += int(rewards.get("coins", 0))
        for item_id, amount in rewards.get("items", {}).items():
            player.inventory.add_item(item_id, amount)
        self.message = f"Missao completa: {QUESTS[quest_id]['title']}."

    def objective_lines(self) -> list[str]:
        lines: list[str] = []
        for quest_id, progress in self.quests.items():
            if progress.completed:
                continue
            quest = QUESTS[quest_id]
            lines.append(quest["title"])
            for objective in quest["objectives"]:
                key = f"{objective['type']}:{objective.get('item') or objective.get('building')}"
                current = min(progress.counters.get(key, 0), objective["amount"])
                lines.append(f"{objective['label']}: {current}/{objective['amount']}")
        return lines

    def to_dict(self) -> dict:
        return {quest_id: progress.to_dict() for quest_id, progress in self.quests.items()}

    @classmethod
    def from_dict(cls, data: dict) -> "QuestSystem":
        system = cls()
        for quest_id, raw in data.items():
            system.quests[quest_id] = QuestProgress(
                quest_id=quest_id,
                active=bool(raw.get("active", True)),
                completed=bool(raw.get("completed", False)),
                counters={str(k): int(v) for k, v in raw.get("counters", {}).items()},
            )
        return system
