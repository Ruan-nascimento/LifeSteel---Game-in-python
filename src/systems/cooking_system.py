from __future__ import annotations

from dataclasses import dataclass

from src.data.food_data import station_allows
from src.data.items_data import ITEMS
from src.data.recipes_data import COOKING_RECIPES
from src.systems.item_system import ITEM_DATABASE, normalize_station_id


@dataclass
class CookingTask:
    raw_item_id: str
    result_item_id: str
    station_id: str
    remaining_time: float
    total_time: float

    def to_dict(self) -> dict:
        return {
            "raw_item_id": self.raw_item_id,
            "result_item_id": self.result_item_id,
            "station_id": self.station_id,
            "remaining_time": self.remaining_time,
            "total_time": self.total_time,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CookingTask":
        return cls(
            raw_item_id=data["raw_item_id"],
            result_item_id=data["result_item_id"],
            station_id=data.get("station_id", "campfire"),
            remaining_time=float(data.get("remaining_time", 0)),
            total_time=float(data.get("total_time", 0)),
        )


class CookingSystem:
    def __init__(self) -> None:
        self.message = "Cozinha pronta."
        self.tasks: list[CookingTask] = []
        self.ready_items: list[str] = []

    def available_recipes(self, player=None, station_id: str | None = None) -> dict[str, dict]:
        recipes: dict[str, dict] = {}
        for raw_id, recipe in COOKING_RECIPES.items():
            if raw_id not in ITEMS or recipe.get("output") not in ITEMS:
                continue
            if station_id and not station_allows(station_id, recipe.get("required_station")):
                continue
            recipes[raw_id] = recipe
        return dict(sorted(recipes.items(), key=lambda item: ITEMS[item[0]]["name"]))

    def cook(self, player, inventory, item_id: str, station_id: str | None) -> dict:
        started = self.start_cooking(player, inventory, item_id, station_id)
        if not started["success"]:
            return started
        task = self.tasks.pop()
        return self.finish_cooking(player, task)

    def start_cooking(self, player, inventory, raw_item_id: str, station_id: str | None) -> dict:
        item_id = raw_item_id
        recipe = COOKING_RECIPES.get(raw_item_id)
        if not recipe:
            return self._failure("Este item nao pode ser cozido.")
        if not station_allows(station_id, recipe.get("required_station")):
            return self._failure("Estacao errada para esta receita.")

        output_id = recipe.get("output")
        if output_id not in ITEMS:
            return self._failure("Resultado de cozimento inexistente.")
        if not self._has_item(player, inventory, item_id):
            return self._failure("Ingrediente insuficiente.")
        if not self._remove_one(player, inventory, item_id):
            return self._failure("Ingrediente insuficiente.")
        total_time = self.calculate_cook_time(recipe, self._station_data(station_id))
        task = CookingTask(
            raw_item_id=raw_item_id,
            result_item_id=output_id,
            station_id=normalize_station_id(station_id) or "campfire",
            remaining_time=total_time,
            total_time=total_time,
        )
        self.tasks.append(task)
        item_name = ITEMS[item_id]["name"]
        output_name = ITEMS[output_id]["name"]
        self.message = f"Voce comecou a cozinhar {item_name}. Resultado: {output_name}."
        return {
            "success": True,
            "message": self.message,
            "item_id": item_id,
            "output_id": output_id,
            "task": task.to_dict(),
        }

    def update(self, dt: float, player=None) -> list[dict]:
        finished: list[dict] = []
        for task in list(self.tasks):
            task.remaining_time -= dt
            if task.remaining_time <= 0:
                self.tasks.remove(task)
                finished.append(self.finish_cooking(player, task))
        return finished

    def finish_cooking(self, player, cooking_task: CookingTask) -> dict:
        if player is None:
            self.ready_items.append(cooking_task.result_item_id)
            return {"success": True, "message": "Preparo pronto.", "task": cooking_task.to_dict()}
        leftover = player.add_item(cooking_task.result_item_id, 1) if hasattr(player, "add_item") else player.inventory.add_item(cooking_task.result_item_id, 1)
        if leftover:
            self.ready_items.append(cooking_task.result_item_id)
            self.message = "Comida pronta, mas o inventario esta cheio."
            return {"success": False, "message": self.message, "task": cooking_task.to_dict()}
        if hasattr(player, "skills"):
            player.skills.add_xp("Cozinhar", 7)
        self.message = f"Voce cozinhou {ITEMS[cooking_task.result_item_id]['name']}."
        return {"success": True, "message": self.message, "output_id": cooking_task.result_item_id}

    def calculate_cook_time(self, item_data: dict, station_data: dict | None) -> float:
        base_time = float(item_data.get("time", 8))
        if "complexity" in item_data:
            base_time = float(self._base_times().get(item_data["complexity"], base_time))
        multiplier = float((station_data or {}).get("speed_multiplier", 1.0))
        return max(0.2, base_time * multiplier)

    def _has_item(self, player, inventory, item_id: str) -> bool:
        if hasattr(player, "count_item"):
            return player.count_item(item_id) >= 1
        return inventory.count(item_id) >= 1

    def _remove_one(self, player, inventory, item_id: str) -> bool:
        if hasattr(player, "pay_items"):
            return player.pay_items({item_id: 1})
        return inventory.remove_item(item_id, 1)

    def _failure(self, message: str) -> dict:
        self.message = message
        return {"success": False, "message": message}

    def _base_times(self) -> dict:
        return ITEM_DATABASE.cooking_data.get("base_cook_time_seconds", {})

    def _station_data(self, station_id: str | None) -> dict | None:
        normalized = normalize_station_id(station_id)
        for station in ITEM_DATABASE.cooking_data.get("stations", []):
            if normalize_station_id(station.get("id")) == normalized or station.get("id") == station_id:
                return station
        return None

    def to_dict(self) -> dict:
        return {
            "tasks": [task.to_dict() for task in self.tasks],
            "ready_items": list(self.ready_items),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CookingSystem":
        system = cls()
        system.tasks = [CookingTask.from_dict(task) for task in data.get("tasks", [])]
        system.ready_items = list(data.get("ready_items", []))
        return system
