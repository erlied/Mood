"""Mood user settings (JSON)."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict
import config

SETTINGS_PATH = config.APP_ROOT / "settings.json"

DEFAULTS: Dict[str, Any] = {
    "blackout_key": "B",
    "panic_key": "X",
    "smart_mix": True,
    "balance_performers": True,
    "video_random_start": True,
    "auto_lock_minutes": 15,
    "default_countdown": 0,
    "repeat_cooldown_sec": 30,
    "tile_size": 184,
}


def load_settings() -> Dict[str, Any]:
    data = dict(DEFAULTS)
    try:
        if SETTINGS_PATH.exists():
            raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                data.update({k: raw[k] for k in DEFAULTS if k in raw})
    except Exception:
        pass
    return data


def save_settings(data: Dict[str, Any]) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged = dict(DEFAULTS)
    merged.update(data)
    SETTINGS_PATH.write_text(json.dumps(merged, indent=2), encoding="utf-8")
