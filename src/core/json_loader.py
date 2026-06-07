from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path, default: Any | None = None) -> Any:
    """Load UTF-8 JSON with controlled fallback for data-driven systems."""
    json_path = Path(path)
    if not json_path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    try:
        return json.loads(json_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {json_path}: {exc}") from exc
