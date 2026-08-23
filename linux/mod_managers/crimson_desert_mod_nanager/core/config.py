"""mod_manager configuration — loaded from config.json at startup."""

import json
from pathlib import Path

_HERE     = Path(__file__).resolve().parent.parent  # mod_manager/
_CFG_PATH = _HERE / 'config.json'

_DEFAULTS: dict = {
    'state_file':     'crimson_modding_state.json',
    'cache_file':     '.papgt_cache.json',
    'mod_prefix':     'mod',
    'overlay_min':    100,
    'backup_keep':    10,
    'mods_dir':       'mods',
    'game_dir':       '',
    'dmm_parser_src': '',
    'cdumm_src':      '',
}


def _load() -> dict:
    if _CFG_PATH.is_file():
        try:
            return {**_DEFAULTS, **json.loads(_CFG_PATH.read_text(encoding='utf-8'))}
        except Exception as e:
            print(f"[WARN]   config.json unreadable ({e}) — using defaults")
    return dict(_DEFAULTS)


_cfg = _load()

STATE_FILE:     str  = str(_cfg['state_file'])
CACHE_FILE:     str  = str(_cfg['cache_file'])
MOD_PREFIX:     str  = str(_cfg['mod_prefix'])
OVERLAY_MIN:    int  = int(_cfg['overlay_min'])
BACKUP_KEEP:    int  = int(_cfg['backup_keep'])
DMM_PARSER_SRC: Path = (
    Path(_cfg['dmm_parser_src']) if _cfg['dmm_parser_src']
    else _HERE / 'dependances'
)


def _find_cdumm_src(mod_manager_dir: Path) -> Path | None:
    # Canonical sibling path: Gaming/Mod-Manager/CrimsonDesert-UltimateModsManager/src
    candidate = (
        mod_manager_dir.parent.parent
        / 'Mod-Manager'
        / 'CrimsonDesert-UltimateModsManager'
        / 'src'
    )
    marker = candidate / 'cdumm' / 'engine' / 'iteminfo_native_parser.py'
    return candidate.resolve() if marker.is_file() else None


CDUMM_SRC: Path | None = (
    Path(_cfg['cdumm_src']).resolve() if _cfg.get('cdumm_src')
    else _find_cdumm_src(_HERE)
)


def mods_dir(base: Path) -> Path:
    """Resolves mods_dir: absolute if absolute path, otherwise relative to mod_manager/."""
    p = Path(_cfg['mods_dir'])
    return p if p.is_absolute() else base / p


def game_dir(base: Path) -> Path:
    """Resolves game_dir: from config if set, otherwise the parent of mod_manager/."""
    raw = str(_cfg.get('game_dir', '')).strip()
    if raw:
        return Path(raw).resolve()
    return base.parent
