from __future__ import annotations

import json
from pathlib import Path

from src.core.settings import Settings


class SaveManager:
    def __init__(self, save_path: Path | None = None) -> None:
        self.save_path = save_path or Settings.SAVE_SLOT
        self.save_path.parent.mkdir(parents=True, exist_ok=True)

    def has_save(self) -> bool:
        return self.save_path.exists()

    def save(self, data: dict) -> None:
        self.save_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self) -> dict | None:
        if not self.save_path.exists():
            return None
        return json.loads(self.save_path.read_text(encoding="utf-8"))
