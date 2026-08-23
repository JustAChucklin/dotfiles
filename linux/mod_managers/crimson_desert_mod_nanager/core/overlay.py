"""Creates an NNNN/ overlay (0.paz + 0.pamt) in the game directory."""

import os
from datetime import datetime
from pathlib import Path

from .config   import MOD_PREFIX, OVERLAY_MIN
from .display  import _ok, _warn
from .packager import build_paz, build_pamt, finalize_pamt, extract_file, COMP_NONE
from .state    import load_state, save_state


def next_overlay_number(game_dir: Path) -> int:
    used = {int(n) for n in os.listdir(game_dir)
            if n.isdigit() and len(n) == 4 and (game_dir / n).is_dir()
            and int(n) >= OVERLAY_MIN}
    n = OVERLAY_MIN
    while n in used:
        n += 1
    return n


def _add_pabgh_companions(
    entries: list[dict], payloads: list[bytes], game_dir: Path
) -> None:
    """Adds the companion vanilla .pabgh for each .pabgb in the overlay.

    The game uses the .pabgh as an offset index to read the .pabgb.
    Without it in the overlay, the game loads the vanilla one — which may have
    stale offsets if the .pabgb structure changed.
    """
    already = {e['filename'].lower() for e in entries}
    additions_e: list[dict] = []
    additions_p: list[bytes] = []

    for e in list(entries):
        fname = e['filename']
        if not fname.lower().endswith('.pabgb'):
            continue
        pabgh_name = fname[:-6] + '.pabgh'
        if pabgh_name.lower() in already:
            continue

        dir_path  = e.get('dir_path', '')
        game_file = f"{dir_path}/{pabgh_name}" if dir_path else pabgh_name
        data = extract_file(game_dir, game_file)
        if data is None:
            _warn(f"  companion .pabgh not found for {fname} — skipped")
            continue

        additions_e.append({
            'dir_path':  dir_path,
            'filename':  pabgh_name,
            'comp_size': len(data),
            'orig_size': len(data),
            'flags':     COMP_NONE,
        })
        additions_p.append(data)
        already.add(pabgh_name.lower())

    entries.extend(additions_e)
    payloads.extend(additions_p)


def write_overlay(entries: list[dict], payloads: list[bytes],
                  mod_name: str, mod_id: str, version: str,
                  game_dir: Path, owner: str) -> bool:
    """Builds and writes a PAZ/PAMT overlay into game_dir."""
    if not entries:
        return False

    _add_pabgh_companions(entries, payloads, game_dir)

    paz_bytes, offsets = build_paz(payloads)
    for e, off in zip(entries, offsets):
        e['paz_offset'] = off
    pamt_bytes  = finalize_pamt(build_pamt(entries, len(paz_bytes)), paz_bytes)

    state    = load_state(game_dir)
    existing = next(
        (folder for folder, info in state['overlays'].items()
         if info.get('mod_id') == mod_id),
        None,
    )
    num         = existing if existing else f"{next_overlay_number(game_dir):04d}"
    overlay_dir = game_dir / num
    overlay_dir.mkdir(exist_ok=True)

    (overlay_dir / '0.paz.tmp').write_bytes(paz_bytes)
    (overlay_dir / '0.pamt.tmp').write_bytes(pamt_bytes)
    (overlay_dir / '0.paz.tmp').replace(overlay_dir / '0.paz')
    (overlay_dir / '0.pamt.tmp').replace(overlay_dir / '0.pamt')
    marker = overlay_dir / f'.{MOD_PREFIX}_{mod_id}'
    if existing:
        for old in overlay_dir.glob(f'.{MOD_PREFIX}_*'):
            if old != marker:
                old.unlink(missing_ok=True)
    marker.write_text(
        f"{owner}  {datetime.now().isoformat(timespec='seconds')}\n"
        f"Mod: {mod_name}  id={mod_id}\nVersion: {version}\n"
    )

    state['overlays'][num] = {
        'owner':     owner,
        'content':   mod_name,
        'mod_id':    mod_id,
        'version':   version,
        'updated':   datetime.now().isoformat(timespec='seconds'),
        'files':     [e['filename'] for e in entries],
        'paz_size':  len(paz_bytes),
        'pamt_size': len(pamt_bytes),
    }
    save_state(game_dir, state)
    _ok(f"'{mod_name}' → {num}/  (PAZ {len(paz_bytes):,} B, PAMT {len(pamt_bytes):,} B)")
    return True
