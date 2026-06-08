from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.core.json_loader import load_json
from src.core.settings import BASE_DIR
from src.data.items_data import ITEMS


QUEST_DATA_PATH = BASE_DIR / "src" / "data" / "quests.json"


def _plain(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", str(value))
    return normalized.encode("ascii", "ignore").decode("ascii").lower()


SKILL_ALIASES = {
    "comunicacao": "Comunicacao",
    "cozinhar": "Cozinhar",
    "pescar": "Pescar",
    "lenhador": "Lenhador",
    "namorador": "Namorador",
    "magia": "Magia",
    "construcao": "Construcao",
    "politica": "Politica",
    "mineracao": "Mineracao",
    "agricultura": "Agricultura",
    "combate": "Combate",
    "defesa": "Defesa",
    "comercio": "Comercio",
    "exploracao": "Exploracao",
    "sobrevivencia": "Sobrevivencia",
    "alquimia": "Alquimia",
    "caca": "Caca",
    "furtividade": "Furtividade",
    "lideranca": "Lideranca",
    "encantamento": "Encantamento",
    "forca": "Forca",
    "coragem": "Coragem",
    "coleta": "Coleta",
    "resistencia": "Resistencia",
    "conhecimento": "Conhecimento",
    "sustentabilidade": "Sustentabilidade",
    "percepcao": "Percepcao",
}


def normalize_skill_name(value: str | None) -> str:
    key = _plain(value).replace(" ", "_")
    return SKILL_ALIASES.get(key, str(value or "Sobrevivencia"))


@dataclass(frozen=True)
class QuestObjective:
    type: str
    target_id: str = "any"
    required: int = 1
    label: str = "Objetivo"
    index: int = 0

    @property
    def key(self) -> str:
        return f"{self.type}:{self.target_id}:{self.index}"

    @classmethod
    def from_dict(cls, data: dict[str, Any], index: int) -> "QuestObjective":
        return cls(
            type=str(data.get("type", "collect")),
            target_id=str(data.get("target_id", data.get("item", data.get("building", "any")))),
            required=max(1, int(data.get("required", data.get("amount", 1)))),
            label=str(data.get("label", "Objetivo")),
            index=index,
        )


@dataclass(frozen=True)
class Quest:
    quest_id: str
    title: str
    level_required: int
    category: str
    description: str
    giver: str
    giver_id: str | None
    location_required: str | None
    requires_discovered_location: bool
    requires_completed_quests: list[str]
    requires_skill_level: dict[str, int]
    auto_start: bool
    objectives: list[QuestObjective]
    rewards: dict[str, Any]
    unique_rewards: list[dict[str, Any]]
    next_quests: list[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Quest":
        return cls(
            quest_id=str(data["id"]),
            title=str(data.get("title", data["id"])),
            level_required=max(1, int(data.get("level_required", 1))),
            category=str(data.get("category", "survival")),
            description=str(data.get("description", "")),
            giver=str(data.get("giver", "Milo Raizforte")),
            giver_id=data.get("giver_id"),
            location_required=data.get("location_required"),
            requires_discovered_location=bool(data.get("requires_discovered_location", False)),
            requires_completed_quests=list(data.get("requires_completed_quests", [])),
            requires_skill_level={
                normalize_skill_name(key): int(value)
                for key, value in (data.get("requires_skill_level", {}) or {}).items()
            },
            auto_start=bool(data.get("auto_start", False)),
            objectives=[QuestObjective.from_dict(raw, index) for index, raw in enumerate(data.get("objectives", []))],
            rewards=dict(data.get("rewards", {})),
            unique_rewards=list(data.get("unique_rewards", [])),
            next_quests=list(data.get("next_quests", [])),
        )


@dataclass
class QuestState:
    quest_id: str
    status: str = "locked"
    counters: dict[str, int] = field(default_factory=dict)
    claimed_rewards: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "quest_id": self.quest_id,
            "status": self.status,
            "counters": dict(self.counters),
            "claimed_rewards": self.claimed_rewards,
        }

    @classmethod
    def from_dict(cls, quest_id: str, data: dict[str, Any]) -> "QuestState":
        status = str(data.get("status", "active" if data.get("active", True) else "locked"))
        completed = bool(data.get("completed", False))
        if completed and "status" not in data:
            status = "claimed"
        return cls(
            quest_id=quest_id,
            status=status,
            counters={str(key): int(value) for key, value in data.get("counters", {}).items()},
            claimed_rewards=bool(data.get("claimed_rewards", status == "claimed")),
        )


class QuestSystem:
    def __init__(self, quest_data: dict[str, Any] | None = None, player=None) -> None:
        self.version = "1.0.0"
        raw = quest_data or load_json(QUEST_DATA_PATH, {"quests": []})
        self.quest_defs: dict[str, Quest] = {
            quest.quest_id: quest
            for quest in (Quest.from_dict(entry) for entry in raw.get("quests", []))
        }
        self.states: dict[str, QuestState] = {
            quest_id: QuestState(quest_id=quest_id)
            for quest_id in self.quest_defs
        }
        self.unique_rewards_received: set[str] = set()
        self.pending_messages: list[str] = []
        self.message = "Missoes prontas."
        self.unlock_quests_for_level(self._player_level(player), player=player, notify=False)

    @property
    def quests(self) -> dict[str, QuestState]:
        return self.states

    def _player_level(self, player=None) -> int:
        if player and hasattr(player, "level"):
            return int(getattr(player.level, "level", 1))
        return 1

    def unlock_quests_for_level(self, level: int, player=None, discovered_locations: set[str] | None = None, notify: bool = True) -> list[str]:
        messages: list[str] = []
        for quest in sorted(self.quest_defs.values(), key=lambda item: (item.level_required, item.quest_id)):
            state = self.states[quest.quest_id]
            if state.status != "locked" or level < quest.level_required:
                continue
            if not self._quest_prerequisites_met(quest, player, discovered_locations or set()):
                continue
            state.status = "active" if quest.auto_start else "available"
            if notify:
                text = f"Nova missao: {quest.title}."
                messages.append(text)
                self.pending_messages.append(text)
        if messages:
            self.message = messages[-1]
        return messages

    def _quest_prerequisites_met(self, quest: Quest, player=None, discovered_locations: set[str] | None = None) -> bool:
        discovered_locations = discovered_locations or set()
        if quest.requires_discovered_location and quest.location_required and quest.location_required not in discovered_locations:
            return False
        for required_quest in quest.requires_completed_quests:
            if self.quest_status(required_quest) != "claimed":
                return False
        if player and quest.requires_skill_level:
            for skill, level in quest.requires_skill_level.items():
                if player.skills.level(skill) < level:
                    return False
        return True

    def accept_quest(self, quest_id: str) -> tuple[bool, str]:
        state = self.states.get(quest_id)
        quest = self.quest_defs.get(quest_id)
        if not state or not quest:
            return False, "Missao inexistente."
        if state.status == "active":
            return True, f"Missao ja ativa: {quest.title}."
        if state.status != "available":
            return False, "Esta missao ainda nao pode ser aceita."
        state.status = "active"
        self.message = f"Missao aceita: {quest.title}."
        return True, self.message

    def update(self, dt: float = 0.0, player=None, discovered_locations: set[str] | None = None) -> None:
        self.unlock_quests_for_level(self._player_level(player), player=player, discovered_locations=discovered_locations, notify=True)

    def update_objective(
        self,
        event_type: str,
        target_id: str | None = None,
        amount: int = 1,
        metadata: dict[str, Any] | None = None,
    ) -> list[str]:
        metadata = metadata or {}
        messages = self._apply_event(event_type, target_id, amount, metadata)
        if event_type in {"buy", "craft"} and target_id:
            messages.extend(self._apply_event("collect", target_id, amount, metadata))
        if event_type in {"buy", "sell"}:
            messages.extend(self._apply_event("trade", target_id or "any", amount, metadata))
        if messages:
            self.message = messages[-1]
        return messages

    def _apply_event(
        self,
        event_type: str,
        target_id: str | None,
        amount: int,
        metadata: dict[str, Any],
    ) -> list[str]:
        messages: list[str] = []
        increment = self._event_amount(event_type, amount, metadata)
        if increment <= 0:
            return messages
        for quest_id, state in self.states.items():
            if state.status != "active":
                continue
            quest = self.quest_defs[quest_id]
            changed = False
            for objective in quest.objectives:
                if not self._matches(objective, event_type, target_id, metadata):
                    continue
                current = state.counters.get(objective.key, 0)
                if current >= objective.required:
                    continue
                state.counters[objective.key] = min(objective.required, current + increment)
                changed = True
            if changed and self.check_completion(quest_id):
                text = f"Missao pronta: {quest.title}. Abra J para resgatar."
                messages.append(text)
        return messages

    def _event_amount(self, event_type: str, amount: int, metadata: dict[str, Any]) -> int:
        if event_type == "earn_coins":
            return max(0, int(metadata.get("coins_earned", metadata.get("coins", amount))))
        if event_type == "skill_xp":
            return max(0, int(metadata.get("xp", amount)))
        return max(1, int(amount))

    def _matches(self, objective: QuestObjective, event_type: str, target_id: str | None, metadata: dict[str, Any]) -> bool:
        if objective.type != event_type:
            return False
        target = objective.target_id
        event_target = str(target_id or metadata.get("target_id") or "any")
        if target in {"any", "*"}:
            return True
        if event_type == "collect" and target == "book":
            data = ITEMS.get(event_target, {})
            return data.get("type") == "book" or event_target.startswith("book")
        if event_type == "cook" and target == "meal":
            data = ITEMS.get(event_target, {})
            return data.get("type") in {"food", "potion", "drink"} and not event_target.startswith("raw_")
        if event_type == "talk" and target == "npc":
            return bool(event_target)
        if event_type == "read_book" and target == "magic":
            return normalize_skill_name(str(metadata.get("skill", ""))) == "Magia" or "magic" in _plain(event_target)
        if event_type == "defeat" and target == "night_enemy":
            return bool(metadata.get("is_night") or metadata.get("night") or event_target == "night_enemy")
        if event_type == "explore" and target == "night":
            return bool(metadata.get("is_night") or metadata.get("night") or event_target == "night")
        if event_type == "return" and target == "camp":
            return event_target == "camp"
        if event_type == "skill_xp":
            skill = normalize_skill_name(str(metadata.get("skill", event_target)))
            return normalize_skill_name(target) == skill
        return target == event_target

    def check_completion(self, quest_id: str) -> bool:
        state = self.states.get(quest_id)
        quest = self.quest_defs.get(quest_id)
        if not state or not quest or state.status != "active":
            return False
        if all(state.counters.get(objective.key, 0) >= objective.required for objective in quest.objectives):
            state.status = "completed"
            return True
        return False

    def claim_reward(self, player, quest_id: str) -> tuple[bool, list[str]]:
        state = self.states.get(quest_id)
        quest = self.quest_defs.get(quest_id)
        if not state or not quest:
            return False, ["Missao inexistente."]
        if state.status == "claimed":
            return False, ["Recompensa ja resgatada."]
        if state.status != "completed":
            return False, ["Complete todos os objetivos antes de resgatar."]

        rewards = quest.rewards or {}
        reward_items = list(rewards.get("items", [])) + list(quest.unique_rewards)
        for entry in reward_items:
            item_id = str(entry.get("id"))
            quantity = int(entry.get("quantity", 1))
            if item_id in self.unique_rewards_received:
                continue
            if hasattr(player, "can_receive_item") and not player.can_receive_item(item_id, quantity):
                return False, ["Inventario cheio para receber recompensas."]

        messages: list[str] = [f"Missao concluida: {quest.title}."]
        xp = int(rewards.get("xp", 0))
        if xp:
            level_ups = player.level.add_xp(xp)
            messages.append(f"+{xp} XP.")
            for level in level_ups:
                messages.append(f"Level {level} alcancado.")
        coins = int(rewards.get("coins", 0))
        if coins:
            player.coins += coins
            messages.append(f"+{coins} ZC.")
        for skill_reward in rewards.get("skill_xp", []):
            skill = normalize_skill_name(skill_reward.get("skill"))
            skill_xp = int(skill_reward.get("xp", 0))
            if skill_xp:
                player.skills.add_xp(skill, skill_xp)
                messages.append(f"+{skill_xp} XP em {skill}.")
        for entry in reward_items:
            item_id = str(entry.get("id"))
            quantity = int(entry.get("quantity", 1))
            if item_id in self.unique_rewards_received:
                continue
            if hasattr(player, "add_item"):
                leftover = player.add_item(item_id, quantity)
            else:
                leftover = player.inventory.add_item(item_id, quantity)
            if leftover <= 0:
                if item_id in {str(item.get("id")) for item in quest.unique_rewards}:
                    self.unique_rewards_received.add(item_id)
                item_name = ITEMS.get(item_id, {}).get("name", item_id)
                messages.append(f"Recebeu {quantity}x {item_name}.")

        state.status = "claimed"
        state.claimed_rewards = True
        self.message = messages[0]
        follow_ups = self._unlock_follow_ups(quest)
        messages.extend(follow_ups)
        completion_events = self.update_objective("claim_quest", quest_id, 1, {"quest_id": quest_id})
        messages.extend(completion_events)
        return True, messages

    def _unlock_follow_ups(self, quest: Quest) -> list[str]:
        messages: list[str] = []
        for quest_id in quest.next_quests:
            state = self.states.get(quest_id)
            follow_up = self.quest_defs.get(quest_id)
            if not state or not follow_up or state.status != "locked":
                continue
            state.status = "active" if follow_up.auto_start else "available"
            messages.append(f"Nova missao: {follow_up.title}.")
        return messages

    def register_collect(self, item_id: str, amount: int = 1) -> None:
        self.update_objective("collect", item_id, amount)

    def register_build(self, building_id: str, amount: int = 1) -> None:
        self.update_objective("build", building_id, amount)

    def update_completion(self, player) -> list[str]:
        self.unlock_quests_for_level(self._player_level(player), player=player, notify=True)
        completed: list[str] = []
        for quest_id, state in self.states.items():
            if state.status == "active" and self.check_completion(quest_id):
                completed.append(quest_id)
        return completed

    def drain_messages(self) -> list[str]:
        messages = list(self.pending_messages)
        self.pending_messages.clear()
        return messages

    def quest_status(self, quest_id: str) -> str:
        state = self.states.get(quest_id)
        return state.status if state else "locked"

    def quests_for_ui(self) -> list[tuple[Quest, QuestState]]:
        order = {"active": 0, "completed": 1, "available": 2, "locked": 3, "claimed": 4}
        result = [(quest, self.states[quest.quest_id]) for quest in self.quest_defs.values()]
        return sorted(result, key=lambda item: (order.get(item[1].status, 9), item[0].level_required, item[0].title))

    def active_quests(self) -> list[tuple[Quest, QuestState]]:
        return [(quest, self.states[quest.quest_id]) for quest in self.quest_defs.values() if self.states[quest.quest_id].status == "active"]

    def completed_quests(self) -> list[tuple[Quest, QuestState]]:
        return [(quest, self.states[quest.quest_id]) for quest in self.quest_defs.values() if self.states[quest.quest_id].status == "completed"]

    def available_quests(self) -> list[tuple[Quest, QuestState]]:
        return [(quest, self.states[quest.quest_id]) for quest in self.quest_defs.values() if self.states[quest.quest_id].status == "available"]

    def objective_progress(self, quest: Quest, state: QuestState) -> list[tuple[QuestObjective, int, int]]:
        return [
            (objective, min(state.counters.get(objective.key, 0), objective.required), objective.required)
            for objective in quest.objectives
        ]

    def objective_lines(self) -> list[str]:
        pairs = self.active_quests()
        if not pairs:
            pairs = self.completed_quests()
        if not pairs:
            pairs = self.available_quests()
        if not pairs:
            return []
        quest, state = pairs[0]
        title_prefix = "Pronta" if state.status == "completed" else "Missao"
        lines = [f"{title_prefix}: {quest.title}"]
        for objective, current, required in self.objective_progress(quest, state):
            lines.append(f"{objective.label}: {current}/{required}")
        if state.status == "completed":
            lines.append("Aperte J para resgatar.")
        return lines

    def to_dict(self) -> dict[str, Any]:
        return self.serialize()

    def serialize(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "states": {quest_id: state.to_dict() for quest_id, state in self.states.items()},
            "unique_rewards_received": sorted(self.unique_rewards_received),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], player=None) -> "QuestSystem":
        return cls.deserialize(data, player=player)

    @classmethod
    def deserialize(cls, data: dict[str, Any] | None, player=None) -> "QuestSystem":
        system = cls(player=player)
        if not data:
            return system
        if "states" in data:
            raw_states = data.get("states", {})
            for quest_id, raw in raw_states.items():
                if quest_id in system.states:
                    system.states[quest_id] = QuestState.from_dict(quest_id, raw)
            system.unique_rewards_received = {str(item_id) for item_id in data.get("unique_rewards_received", [])}
        else:
            system._load_legacy_state(data)
        system.unlock_quests_for_level(system._player_level(player), player=player, notify=False)
        return system

    def _load_legacy_state(self, data: dict[str, Any]) -> None:
        for quest_id, raw in data.items():
            if quest_id not in self.states:
                continue
            state = QuestState.from_dict(quest_id, raw)
            quest = self.quest_defs[quest_id]
            converted: dict[str, int] = {}
            for key, value in state.counters.items():
                parts = key.split(":")
                if len(parts) < 2:
                    continue
                event_type, target_id = parts[0], parts[1]
                for objective in quest.objectives:
                    if objective.type == event_type and objective.target_id == target_id:
                        converted[objective.key] = int(value)
            if converted:
                state.counters = converted
            self.states[quest_id] = state
