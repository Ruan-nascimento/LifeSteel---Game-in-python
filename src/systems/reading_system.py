from __future__ import annotations

from src.systems.item_system import ITEM_DATABASE, ItemDatabase, normalize_skill_name
from src.systems.passive_bonus_system import PassiveBonusSystem


class ReadingSystem:
    def __init__(self, database: ItemDatabase | None = None) -> None:
        self.database = database or ITEM_DATABASE
        self.passives = PassiveBonusSystem()
        self.message = "Leitura pronta."

    def start_reading(self, player, inventory, book_id: str) -> dict:
        if not self.database.item_exists(book_id):
            return self._failure("Livro inexistente.")
        data = self.database.get_item(book_id)
        if data.get("type") != "book":
            return self._failure("Este item nao e um livro.")
        if not inventory.has_item(book_id, 1):
            return self._failure("Livro nao encontrado no inventario.")
        if getattr(player, "current_reading", None):
            return self._failure("Voce ja esta lendo um livro.")
        if book_id in getattr(player, "read_books", set()):
            self.message = "Voce ja leu este livro. Pode reler pela historia, mas a recompensa nao repete."
            return {
                "success": True,
                "message": self.message,
                "book_id": book_id,
                "repeat": True,
            }
        days_required = int((data.get("functionalities") or {}).get("reading_days", data.get("reading_days", 1)))
        player.current_reading = {
            "book_id": book_id,
            "days_required": max(1, days_required),
            "days_read": 0,
        }
        self.message = f"Voce comecou a ler {data.get('name', book_id)}."
        return {"success": True, "message": self.message, "book_id": book_id}

    def read_day_progress(self, player) -> dict:
        current = getattr(player, "current_reading", None)
        if not current:
            return self._failure("Nenhum livro em leitura.")
        current["days_read"] = int(current.get("days_read", 0)) + 1
        if current["days_read"] >= int(current.get("days_required", 1)):
            return self.finish_book(player, current["book_id"])
        remaining = int(current["days_required"]) - int(current["days_read"])
        self.message = f"Faltam {remaining} dias de leitura."
        return {"success": True, "message": self.message, "current_reading": current}

    def finish_book(self, player, book_id: str) -> dict:
        if book_id in getattr(player, "read_books", set()):
            player.current_reading = None
            return self._failure("Recompensa deste livro ja foi aplicada.")
        data = self.database.get_item(book_id)
        messages = self.apply_book_rewards(player, data)
        if not hasattr(player, "read_books"):
            player.read_books = set()
        player.read_books.add(book_id)
        player.current_reading = None
        self.message = f"Voce terminou de ler {data.get('name', book_id)}."
        functionalities = data.get("functionalities") or {}
        return {
            "success": True,
            "message": self.message,
            "rewards": messages,
            "book_id": book_id,
            "target_skill": normalize_skill_name(functionalities.get("target_skill")),
            "skill_xp": int(functionalities.get("skill_xp_reward", 0) or 0),
        }

    def apply_book_rewards(self, player, book_data: dict) -> list[str]:
        functionalities = book_data.get("functionalities") or {}
        messages: list[str] = []
        target_skill = normalize_skill_name(functionalities.get("target_skill"))
        xp_reward = int(functionalities.get("skill_xp_reward", 0) or 0)
        if xp_reward and hasattr(player, "skills"):
            player.skills.add_xp(target_skill, xp_reward)
            messages.append(f"+{xp_reward} XP em {target_skill}.")
        if functionalities.get("can_unlock_skill") and hasattr(player, "skills"):
            player.skills.unlock_skill(target_skill)
            messages.append(f"Nova habilidade desbloqueada: {target_skill}.")
        for recipe_id in functionalities.get("unlocks_recipes", []) or []:
            if not hasattr(player, "unlocked_recipes"):
                player.unlocked_recipes = set()
            player.unlocked_recipes.add(recipe_id)
            messages.append(f"Receita desbloqueada: {recipe_id}.")
        for ability_id in functionalities.get("unlocks_abilities", []) or []:
            if not hasattr(player, "unlocked_abilities"):
                player.unlocked_abilities = set()
            player.unlocked_abilities.add(ability_id)
            messages.append(f"Habilidade especial desbloqueada: {ability_id}.")
        passive_bonus = functionalities.get("passive_bonus") or {}
        if passive_bonus:
            self.passives.apply_bonus(player, passive_bonus, source_id=book_data["id"])
            messages.append("Bonus passivo aplicado.")
        return messages

    def get_current_book_progress(self, player) -> dict | None:
        current = getattr(player, "current_reading", None)
        return dict(current) if current else None

    def _failure(self, message: str) -> dict:
        self.message = message
        return {"success": False, "message": message}
