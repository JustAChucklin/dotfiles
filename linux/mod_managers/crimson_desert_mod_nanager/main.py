#!/usr/bin/env python3
"""main.py — Crimson Desert mod manager"""

import argparse
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent

from core.config    import mods_dir as _mods_dir, game_dir as _game_dir
from core.display   import _die, _info, _ok
from core.installer import uninstall_mod, cmd_status, cmd_dry_run, cmd_update
from core.state     import load_state
from core.patcher   import cmd_dry_run as cmd_patch_dry_run, cmd_update as cmd_patch_update
from core           import bin64, papgt as _papgt


# ── Contextual help ───────────────────────────────────────────────────────────

_HELP_GENERAL = """\
Crimson Desert Mod Manager

usage: ./main.py <command> [options]

commands:
  --install        Scan and interactively install all mods
  --update         Install only mods with a newer available version
  --status         Status of all mods (browser, ASI, ReShade, patches)
  --uninstall ID   Uninstall a browser overlay by its id
  --papgt          Rebuild meta/0.papgt

global option:
  --dir DIR        Game directory (default: parent folder of the script)
  -h, --help       Contextual help (e.g.: --install -h, --papgt -h)
"""

_HELP_INSTALL = """\
./main.py --install [options]

  Scans mods in mods/, detects conflicts and offers
  interactive installation. Also installs ASI, ReShade
  and JSON patch mods (mods/asi/, mods/reshade/, mods/patch/).

options:
  --force, -f   Reinstall even if mods are already up to date
  --yes,   -y   Apply without asking for confirmation
                (includes rebuilding meta/0.papgt at the end)
  --dir    DIR  Game directory (default: parent folder of the script)

examples:
  ./main.py --install
  ./main.py --install --force
  ./main.py --install --yes
  ./main.py --install --force --yes
"""

_HELP_STATUS = """\
./main.py --status

  Displays the status of all mods: browser (PAZ/PAMT), ASI/DLL,
  ReShade and JSON patches. Shows for each mod whether it is installed,
  up to date or pending an update.

option:
  --dir DIR   Game directory (default: parent folder of the script)

example:
  ./main.py --status
"""

_HELP_UNINSTALL = """\
./main.py --uninstall ID [options]

  Removes the NNNN/ overlay corresponding to the browser mod identified by ID.
  Then offers to rebuild meta/0.papgt.

options:
  --yes, -y   Apply without asking for confirmation
  --dir DIR   Game directory (default: parent folder of the script)

examples:
  ./main.py --uninstall my-mod
  ./main.py --uninstall my-mod --yes
"""

_HELP_PAPGT = """\
./main.py --papgt [options]

  Rebuilds the meta/0.papgt file from installed overlays
  and the vanilla cache. An automatic backup is created before each
  modification (10 backups kept).

options:
  --recache   Recomputes vanilla hashes from .pamt files
              Use after a game update to avoid a corrupted papgt.
  --restore   Restore a previous backup of 0.papgt (interactive menu)
  --yes, -y   Apply without asking for confirmation
  --dir DIR   Game directory (default: parent folder of the script)

examples:
  ./main.py --papgt
  ./main.py --papgt --yes
  ./main.py --papgt --recache        # after a game update
  ./main.py --papgt --restore        # choose a backup to restore
"""


# ── Parser ────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument('--install',         action='store_true')
    parser.add_argument('--update',          action='store_true')
    parser.add_argument('--force',    '-f',  action='store_true')
    parser.add_argument('--yes',      '-y',  action='store_true')
    parser.add_argument('--status',          action='store_true')
    parser.add_argument('--uninstall',       default=None, metavar='ID')
    parser.add_argument('--papgt',           action='store_true')
    parser.add_argument('--recache',         action='store_true')
    parser.add_argument('--restore',         action='store_true')
    parser.add_argument('--dir',             default=None, metavar='DIR')
    return parser


def _check_deps() -> None:
    try:
        import lz4.block  # noqa: F401
    except ImportError:
        _die("Missing package: pip install lz4")
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher  # noqa: F401
    except ImportError:
        _die("Missing package: pip install cryptography")


def _propose_papgt(game_dir: Path, yes: bool) -> None:
    print()
    if yes:
        _papgt.run(game_dir, yes=True); return
    try:
        rep = input("  Rebuild meta/0.papgt now? [y/N]  ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print(); rep = ''
    if rep in ('y', 'yes'):
        _papgt.run(game_dir, yes=True)
    else:
        _info("Run anytime: ./main.py --papgt")


def main() -> None:
    # ── Contextual help — before argparse to avoid parsing conflicts ──────────
    raw = sys.argv[1:]
    if '-h' in raw or '--help' in raw:
        if '--install'   in raw: print(_HELP_INSTALL)
        elif '--papgt'   in raw: print(_HELP_PAPGT)
        elif '--status'  in raw: print(_HELP_STATUS)
        elif '--uninstall' in raw: print(_HELP_UNINSTALL)
        else:                    print(_HELP_GENERAL)
        return

    parser = _build_parser()
    args   = parser.parse_args()

    game_dir = Path(args.dir).resolve() if args.dir else _game_dir(_HERE)
    mods_dir = _mods_dir(_HERE)

    # ── papgt ──────────────────────────────────────────────────────────────────
    if args.papgt:
        _papgt.run(game_dir, recache=args.recache, restore=args.restore, yes=args.yes)
        return

    # ── status ─────────────────────────────────────────────────────────────────
    if args.status:
        if not mods_dir.is_dir():
            _die(f"mods/ directory not found: {mods_dir}")
        cmd_status(game_dir, mods_dir, load_state(game_dir))
        return

    # ── uninstall ──────────────────────────────────────────────────────────────
    if args.uninstall:
        if uninstall_mod(args.uninstall, game_dir, yes=args.yes):
            _propose_papgt(game_dir, args.yes)
        return

    # ── update ────────────────────────────────────────────────────────────────
    if args.update:
        if not mods_dir.is_dir():
            _die(f"mods/ directory not found: {mods_dir}")
        _check_deps()
        changed  = cmd_update(mods_dir, game_dir, yes=args.yes)
        changed += cmd_patch_update(mods_dir / 'patch', game_dir, yes=args.yes)
        changed += bin64.cmd_update(mods_dir / 'asi',     game_dir / 'bin64', bin64.ASI,     yes=args.yes)
        changed += bin64.cmd_update(mods_dir / 'reshade', game_dir / 'bin64', bin64.RESHADE, yes=args.yes)
        if not changed:
            _ok("All mods are already up to date.")
        elif changed:
            _propose_papgt(game_dir, args.yes)
        return

    # ── install ────────────────────────────────────────────────────────────────
    if args.install:
        if not mods_dir.is_dir():
            _die(f"mods/ directory not found: {mods_dir}")
        _check_deps()
        cmd_dry_run(mods_dir, game_dir, force=args.force, yes=args.yes)
        cmd_patch_dry_run(mods_dir / 'patch', game_dir, force=args.force, yes=args.yes)
        bin64.cmd_dry_run(mods_dir / 'asi',     game_dir / 'bin64', bin64.ASI,     force=args.force, yes=args.yes)
        bin64.cmd_dry_run(mods_dir / 'reshade', game_dir / 'bin64', bin64.RESHADE, force=args.force, yes=args.yes)
        _propose_papgt(game_dir, args.yes)
        return

    print(_HELP_GENERAL)


if __name__ == '__main__':
    main()
