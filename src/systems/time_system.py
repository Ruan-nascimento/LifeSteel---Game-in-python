from __future__ import annotations

from src.core.settings import Settings


class TimeSystem:
    DAY_START = 6 * 60
    SUNSET_START = 17 * 60 + 30
    NIGHT_START = 19 * 60
    DAWN_START = 4 * 60 + 30

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

    def get_time_string(self) -> str:
        return f"Dia {self.day} - {self.hour:02d}:{self.minute:02d}"

    def clock_text(self) -> str:
        return self.get_time_string()

    def get_day_phase(self) -> str:
        if self.DAWN_START <= self.minutes < self.DAY_START:
            return "dawn"
        if self.DAY_START <= self.minutes < self.SUNSET_START:
            return "day"
        if self.SUNSET_START <= self.minutes < self.NIGHT_START:
            return "sunset"
        return "night"

    def is_day(self) -> bool:
        return self.get_day_phase() == "day"

    def is_sunset(self) -> bool:
        return self.get_day_phase() == "sunset"

    def is_dawn(self) -> bool:
        return self.get_day_phase() == "dawn"

    def is_night(self) -> bool:
        return self.get_day_phase() == "night"

    @property
    def night(self) -> bool:
        return self.is_night()

    def shop_is_open(self) -> bool:
        return 7 <= self.hour < 22

    def get_darkness_alpha(self) -> int:
        phase = self.get_day_phase()
        if phase == "day":
            return 0
        if phase == "sunset":
            progress = (self.minutes - self.SUNSET_START) / max(1, self.NIGHT_START - self.SUNSET_START)
            return int(42 + progress * 168)
        if phase == "dawn":
            progress = (self.minutes - self.DAWN_START) / max(1, self.DAY_START - self.DAWN_START)
            return int(190 * (1.0 - progress))
        return 210

    def light_alpha(self) -> int:
        return self.get_darkness_alpha()

    def to_dict(self) -> dict:
        return {"day": self.day, "minutes": self.minutes}

    @classmethod
    def from_dict(cls, data: dict) -> "TimeSystem":
        time = cls()
        time.day = int(data.get("day", 1))
        time.minutes = int(data.get("minutes", Settings.START_HOUR * 60 + Settings.START_MINUTE))
        return time
