import random


class WeatherSystem:
    WEATHERS = ["Ensolarado", "Chuvoso", "Nublado", "Tempestade", "Nevoeiro"]

    def __init__(self) -> None:
        self.current = "Ensolarado"
        self._timer = 0.0

    def update(self, dt: float, new_day: bool = False) -> None:
        self._timer += dt
        if new_day or self._timer > 420:
            self._timer = 0.0
            self.current = random.choices(
                self.WEATHERS,
                weights=[42, 22, 18, 8, 10],
                k=1,
            )[0]

    def movement_modifier(self) -> float:
        if self.current == "Tempestade":
            return 0.90
        if self.current == "Nevoeiro":
            return 0.95
        return 1.0

    def fishing_bonus(self) -> float:
        return 1.15 if self.current in {"Chuvoso", "Tempestade"} else 1.0

    def overlay(self) -> tuple[tuple[int, int, int], int]:
        if self.current == "Chuvoso":
            return (43, 80, 108), 28
        if self.current == "Tempestade":
            return (28, 42, 65), 48
        if self.current == "Nevoeiro":
            return (205, 216, 207), 44
        if self.current == "Nublado":
            return (126, 134, 128), 22
        return (255, 255, 255), 0

    def to_dict(self) -> dict:
        return {"current": self.current, "timer": self._timer}

    @classmethod
    def from_dict(cls, data: dict) -> "WeatherSystem":
        weather = cls()
        weather.current = data.get("current", "Ensolarado")
        weather._timer = float(data.get("timer", 0))
        return weather
