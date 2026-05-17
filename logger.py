# =============================================================================
# PROJECT ECHO – logger.py
# Lightweight singleton logger for events and periodic statistics.
# No project-internal imports – safe to import from anywhere.
# =============================================================================

from __future__ import annotations

import datetime
import sys
from typing import TYPE_CHECKING

from settings import (
    LOG_TO_CONSOLE, LOG_TO_FILE, LOG_FILE,
    HUNGER_THRESHOLD,
)

if TYPE_CHECKING:
    from world import World


# =============================================================================
class Logger:
    """
    Central event and statistics logger.

    Usage
    -----
    from logger import get_logger
    get_logger().log_event("FOOD_FOUND", "ate at (x, y)", "ECHO-03")
    get_logger().increment_social()
    get_logger().log_stats(world)
    """

    def __init__(self) -> None:
        self._social_count : int             = 0
        self._file                           = None
        self._session_start : datetime.datetime = datetime.datetime.now()

        if LOG_TO_FILE:
            self._file = open(LOG_FILE, "a", encoding="utf-8")
            self._write_raw(
                f"\n{'=' * 60}\n"
                f"  PROJECT ECHO – Session {self._session_start.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"{'=' * 60}\n"
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log_event(
        self,
        event_type : str,
        message    : str,
        label      : str = "",
    ) -> None:
        """Log a named event with optional creature label."""
        ts   = self._timestamp()
        tag  = f"[{event_type:<13}]"
        who  = f"{label:<8}" if label else " " * 8
        line = f"[{ts}] {tag} {who} | {message}"
        self._emit(line)

    def log_stats(self, world: "World") -> None:
        """Compute and log a statistics snapshot from alive creatures only."""
        creatures = [c for c in world.creatures if c.alive]
        if not creatures:
            return

        pop         = len(creatures)
        avg_hunger  = sum(c.hunger for c in creatures) / pop
        avg_energy  = sum(c.energy for c in creatures) / pop
        hungry      = sum(1 for c in creatures if c.hunger >= HUNGER_THRESHOLD)
        social_evts = self._social_count
        self._social_count = 0                   # reset interval counter

        ts   = self._timestamp()
        line = (
            f"[{ts}] [{'STATS':<13}] {'':8} | "
            f"pop={pop}  "
            f"avg_hunger={avg_hunger:5.1f}  "
            f"avg_energy={avg_energy:5.1f}  "
            f"hungry={hungry}  "
            f"social_events={social_evts}"
        )
        self._emit(line)

    def increment_social(self) -> None:
        """Called each time a social interaction occurs."""
        self._social_count += 1

    def close(self) -> None:
        """Flush and close the log file."""
        if self._file:
            self._file.flush()
            self._file.close()
            self._file = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _emit(self, line: str) -> None:
        if LOG_TO_CONSOLE:
            print(line, flush=True)
        if LOG_TO_FILE and self._file:
            self._file.write(line + "\n")
            self._file.flush()

    def _write_raw(self, text: str) -> None:
        if self._file:
            self._file.write(text)
            self._file.flush()

    @staticmethod
    def _timestamp() -> str:
        now = datetime.datetime.now()
        return now.strftime("%H:%M:%S.") + f"{now.microsecond // 1000:03d}"


# =============================================================================
# Module-level singleton
# =============================================================================

_instance: Logger | None = None


def get_logger() -> Logger:
    """Return the global Logger singleton, creating it on first call."""
    global _instance
    if _instance is None:
        _instance = Logger()
    return _instance
