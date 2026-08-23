"""Installed overlay state management (crimson_modding_state.json)."""

import json
from datetime import datetime
from pathlib import Path

from .config  import STATE_FILE
from .display import _warn


def load_state(game_dir: Path) -> dict:
    path = game_dir / STATE_FILE
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except Exception as e:
            _warn(f"Cannot read {STATE_FILE}: {e} — using empty state")
    return {
        "version":           1,
        "last_updated":      datetime.now().isoformat(timespec='seconds'),
        "game_path":         str(game_dir),
        "overlays":          {},
    }


def save_state(game_dir: Path, state: dict) -> None:
    state['last_updated'] = datetime.now().isoformat(timespec='seconds')
    path = game_dir / STATE_FILE
    tmp  = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding='utf-8')
    tmp.replace(path)
