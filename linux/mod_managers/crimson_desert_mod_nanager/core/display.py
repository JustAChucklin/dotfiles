"""Terminal output — ANSI colors and log helpers."""

import sys

GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
CYAN   = "\033[36m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def _ok(msg: str)   -> None: print(f"{GREEN}[OK]{RESET}     {msg}")
def _info(msg: str) -> None: print(f"{CYAN}[INFO]{RESET}   {msg}")
def _warn(msg: str) -> None: print(f"{YELLOW}[WARN]{RESET}   {msg}")
def _err(msg: str)  -> None: print(f"{RED}[ERROR]{RESET}  {msg}", file=sys.stderr)
def _die(msg: str)  -> None: _err(msg); sys.exit(1)
