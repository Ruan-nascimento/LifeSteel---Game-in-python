from src.core.settings import Settings


class TimeSystem:
    def __init__(self) -> None:
        self.day = 1
        self.minutes = Settings.START_HOUR * 60 + Settings.START_MINUTE
        self._accumulator = 0.0

    def update(self, dt: float) -> bool:
        minutes_per_second = 24 * 60 / Settings.REAL_SECONDS_PER_GAME_DAY
        before_day = self.day
        self._accumulator += dt * minutes_per_second
        while self._accumulator >= 1:
            self.minutes += 1
            self._accumulator -= 1
            if self.minutes >= 24 * 60:
                self.minutes = 0
                self.day += 1
        return self.day != before_day

    @property
    def hour(self) -> int:
        return self.minutes // 60

    @property
    def minute(self) -> int:
        return self.minutes % 60

    @property
    def is_night(self) -> bool:
        return self.hour < 6 or self.hour >= 20

    def clock_text(self) -> str:
        return f"Dia {self.day} - {self.hour:02d}:{self.minute:02d}"

    def shop_is_open(self) -> bool:
        return 7 <= self.hour < 22

    def light_alpha(self) -> int:
        if 6 <= self.hour < 18:
            return 0
        if 18 <= self.hour < 20:
            return int((self.hour - 18) / 2 * 90)
        if 4 <= self.hour < 6:
            return int((6 - self.hour) / 2 * 90)
        return 110

    def to_dict(self) -> dict:
        return {"day": self.day, "minutes": self.minutes}

    @classmethod
    def from_dict(cls, data: dict) -> "TimeSystem":
        time = cls()
        time.day = int(data.get("day", 1))
        time.minutes = int(data.get("minutes", Settings.START_HOUR * 60 + Settings.START_MINUTE))
        return time
