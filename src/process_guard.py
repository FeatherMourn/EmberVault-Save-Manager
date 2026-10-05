"""Best-effort game-running detection with a testable process boundary."""

from __future__ import annotations

import subprocess


GAME_PROCESS_NAMES = frozenset({"enshrouded.exe", "enshroudedserver.exe"})


def is_game_running(process_names: frozenset[str] = GAME_PROCESS_NAMES) -> bool:
    """Return whether a known Enshrouded process is currently listed."""
    try:
        result = subprocess.run(["tasklist", "/fo", "csv", "/nh"],
                                capture_output=True, text=True, check=False)
    except OSError:
        return False
    for line in result.stdout.splitlines():
        name = line.split(",", 1)[0].strip('"').casefold()
        if name in {item.casefold() for item in process_names}:
            return True
    return False
