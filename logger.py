# =============================================================================
# PROJECT ECHO – logger.py
# Session-based logging framework.
#
# Each simulation run creates a unique timestamped file in logs/.
# Public API is backward-compatible: log_event / log_stats / increment_social.
# New API:  start_session(world)       – write header after world is ready
#           log_relationship(...)      – BEST_FRIEND / RIVALRY events
#           log_lifetime_summary(c)    – full life recap at death
#           increment_food_consumed()  – global food counter
#           close(world)               – write session summary, flush, close
# =============================================================================

from __future__ import annotations

import datetime
import os
import sys
from typing import TYPE_CHECKING

from settings import (
    LOG_TO_CONSOLE, LOG_TO_FILE, LOG_DIR,
    HUNGER_THRESHOLD, CREATURE_COUNT, FOOD_INITIAL_COUNT,
)

if TYPE_CHECKING:
    from world import World
    from creature import Creature


# =============================================================================
_W = 20   # event-type column width


class Logger:
    """
    Central event and statistics logger.

    Session lifecycle
    -----------------
    1. get_logger()              – creates Logger, opens log file
    2. get_logger().start_session(world)  – writes header with world snapshot
    3. [simulation runs] …
    4. get_logger().close(world) – writes session summary, closes file
    """

    def __init__(self) -> None:
        self._social_count  : int   = 0
        self._file                  = None
        self._log_path      : str   = ""
        self._session_start         = datetime.datetime.now()

        # Session-wide analytics
        self._max_population        : int   = 0
        self._total_food_consumed   : int   = 0
        self._total_social          : int   = 0

        # Per-creature death records (for session summary)
        self._death_records : list[dict] = []

        if LOG_TO_FILE:
            os.makedirs(LOG_DIR, exist_ok=True)
            fname          = "echo_" + self._session_start.strftime("%Y-%m-%d_%H-%M-%S") + ".log"
            self._log_path = os.path.join(LOG_DIR, fname)
            self._file     = open(self._log_path, "w", encoding="utf-8")

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def start_session(self, world: "World") -> None:
        """
        Write session header with world snapshot.
        Must be called after World() is fully initialised.
        """
        from settings import (
            FPS, HUNGER_DECAY_RATE, ENERGY_REST_RATE,
            ENERGY_DECAY_WANDER, ENERGY_DECAY_SEEK,
            FOOD_SPAWN_INTERVAL, FOOD_SPAWN_BATCH, FOOD_MAX_COUNT,
            BIOME_COUNT,
        )
        ts        = self._session_start.strftime("%Y-%m-%d %H:%M:%S")
        sep_thick = "=" * 62
        sep_thin  = "-" * 62

        biome_summary = "  ".join(
            f"{b.type}({b.rate:.1f}x)" for b in world.biomes
        )

        header = "\n".join([
            sep_thick,
            f"  PROJECT ECHO  –  Session {ts}",
            sep_thick,
            f"  File              : {self._log_path or '(console only)'}",
            sep_thin,
            f"  Initial population: {CREATURE_COUNT}",
            f"  Biomes            : {len(world.biomes)}  →  {biome_summary}",
            f"  Initial food      : {FOOD_INITIAL_COUNT}  (cap {FOOD_MAX_COUNT},"
            f" spawn {FOOD_SPAWN_BATCH} / {FOOD_SPAWN_INTERVAL}s)",
            sep_thin,
            f"  Hunger decay      : {HUNGER_DECAY_RATE}/s",
            f"  Energy wander/seek: {ENERGY_DECAY_WANDER}/{ENERGY_DECAY_SEEK} /s",
            f"  Energy rest rate  : {ENERGY_REST_RATE}/s",
            f"  Target FPS        : {FPS}",
            sep_thick,
            "",
        ])

        if LOG_TO_CONSOLE:
            print(header, flush=True)
        if self._file:
            self._file.write(header + "\n")
            self._file.flush()

    def close(self, world: "World | None" = None) -> None:
        """Write session summary (if world provided), flush, close file."""
        if world is not None:
            self._write_session_summary(world)
        if self._file:
            self._file.flush()
            self._file.close()
            self._file = None

    # ------------------------------------------------------------------
    # Core event logging
    # ------------------------------------------------------------------

    def log_event(
        self,
        event_type : str,
        message    : str,
        label      : str = "",
    ) -> None:
        """Log a named event with optional creature label."""
        ts   = self._timestamp()
        tag  = f"[{event_type:<{_W}}]"
        who  = f"{label:<8}" if label else " " * 8
        line = f"[{ts}] {tag} {who} | {message}"
        self._emit(line)

    def log_stats(self, world: "World") -> None:
        """Compute and log a periodic statistics snapshot."""
        creatures = [c for c in world.creatures if c.alive]
        if not creatures:
            return

        pop = len(creatures)
        self._max_population = max(self._max_population, pop)

        avg_hunger  = sum(c.hunger for c in creatures) / pop
        avg_energy  = sum(c.energy for c in creatures) / pop
        hungry      = sum(1 for c in creatures if c.hunger >= HUNGER_THRESHOLD)
        social_evts = self._social_count
        self._social_count = 0

        contested       = sum(1 for f in world.foods if f.claimed_by is not None)
        contested_ratio = contested / max(1, len(world.foods))

        ts   = self._timestamp()
        line = (
            f"[{ts}] [{'STATS':<{_W}}] {'':8} | "
            f"pop={pop}  "
            f"avg_hunger={avg_hunger:5.1f}  "
            f"avg_energy={avg_energy:5.1f}  "
            f"hungry={hungry}  "
            f"social_events={social_evts}  "
            f"contested_food={contested_ratio:.0%}"
        )
        self._emit(line)

    # ------------------------------------------------------------------
    # Relationship events
    # ------------------------------------------------------------------

    def log_relationship(
        self,
        event_type : str,       # BEST_FRIEND | RIVALRY | RELATIONSHIP_GAIN | RELATIONSHIP_LOSS
        label_a    : str,
        label_b    : str,
        affinity   : float,
        delta      : float | None = None,
    ) -> None:
        delta_str = f" (Δ{delta:+.1f})" if delta is not None else ""
        msg = f"with {label_b:<8} | affinity={affinity:6.1f}{delta_str}"
        self.log_event(event_type, msg, label_a)

    # ------------------------------------------------------------------
    # Lifetime summary (called from Creature._die)
    # ------------------------------------------------------------------

    def log_lifetime_summary(self, creature: "Creature") -> None:
        """Log a complete life recap and store it for the session summary."""
        sep = "-" * 62

        # Dominant state by time
        state_times = {
            "WANDER"    : creature.time_wandering,
            "SEEK_FOOD" : creature.time_seeking_food,
            "REST"      : creature.time_resting,
            "SOCIALIZE" : creature.time_socializing,
        }
        dominant = max(state_times, key=state_times.get)

        # Best friend
        best_friend_label    = "none"
        best_friend_affinity = 0.0
        if creature.relationships:
            best_id   = max(creature.relationships,
                            key=lambda k: creature.relationships[k]["affinity"])
            best_data = creature.relationships[best_id]
            if best_data["affinity"] > 0:
                best_friend_label    = best_data["label"]
                best_friend_affinity = best_data["affinity"]

        lines = [
            sep,
            f"  LIFE SUMMARY  –  {creature.label}",
            f"  Lifespan            : {creature._lifespan:.1f}s",
            f"  Cause of death      : {creature._cause_of_death}",
            f"  Food eaten          : {creature.food_eaten}",
            f"  Distance travelled  : {creature.distance_travelled:.0f} px",
            f"  Social interactions : {creature.social_interactions}",
            f"  Time resting        : {creature.time_resting:.1f}s",
            f"  Time socializing    : {creature.time_socializing:.1f}s",
            f"  Time seeking food   : {creature.time_seeking_food:.1f}s",
            f"  Dominant state      : {dominant}",
            f"  Best friend         : {best_friend_label}"
            + (f"  (affinity={best_friend_affinity:.1f})" if best_friend_affinity > 0 else ""),
            f"  Personality         : risk={creature.risk_tolerance:.2f}"
            f"  lazy={creature.laziness:.2f}"
            f"  social={creature.social_dependency:.2f}"
            f"  greed={creature.food_greed:.2f}",
            sep,
        ]
        for line in lines:
            self._emit(line)

        # Store for session summary
        self._death_records.append({
            "label"              : creature.label,
            "lifespan"           : creature._lifespan,
            "food_eaten"         : creature.food_eaten,
            "distance_travelled" : creature.distance_travelled,
            "social_interactions": creature.social_interactions,
            "dominant_state"     : dominant,
            "cause"              : creature._cause_of_death,
            "best_friend"        : best_friend_label,
            "personality"        : {
                "risk"   : round(creature.risk_tolerance, 2),
                "lazy"   : round(creature.laziness, 2),
                "social" : round(creature.social_dependency, 2),
                "greed"  : round(creature.food_greed, 2),
            },
        })

    # ------------------------------------------------------------------
    # Counters
    # ------------------------------------------------------------------

    def increment_social(self) -> None:
        self._social_count  += 1
        self._total_social  += 1

    def increment_food_consumed(self) -> None:
        self._total_food_consumed += 1

    # ------------------------------------------------------------------
    # Session summary
    # ------------------------------------------------------------------

    def _write_session_summary(self, world: "World") -> None:
        alive   = [c for c in world.creatures if c.alive]
        records = self._death_records
        sep     = "=" * 62
        thin    = "-" * 62

        lines = [
            "",
            sep,
            "  SESSION SUMMARY",
            sep,
            f"  Max population         : {self._max_population}",
            f"  Final population       : {len(alive)}",
            f"  Creatures that died    : {len(records)}",
            f"  Total food consumed    : {self._total_food_consumed}",
            f"  Total social events    : {self._total_social}",
        ]

        if records:
            avg_ls      = sum(r["lifespan"] for r in records) / len(records)
            longest     = max(records, key=lambda r: r["lifespan"])
            most_social = max(records, key=lambda r: r["social_interactions"])
            best_food   = max(records, key=lambda r: r["food_eaten"])
            most_travel = max(records, key=lambda r: r["distance_travelled"])

            lines += [
                thin,
                f"  Avg lifespan (dead)    : {avg_ls:.1f}s",
                f"  Longest survivor       : {longest['label']}"
                f"  ({longest['lifespan']:.1f}s, {longest['food_eaten']} meals)",
                f"  Most social            : {most_social['label']}"
                f"  ({most_social['social_interactions']} interactions)",
                f"  Best forager           : {best_food['label']}"
                f"  ({best_food['food_eaten']} meals)",
                f"  Most travelled         : {most_travel['label']}"
                f"  ({most_travel['distance_travelled']:.0f} px)",
            ]

        if alive:
            lines += [thin, "  Still alive:"]
            for c in alive:
                lines.append(
                    f"    {c.label:<8}"
                    f"  lifespan={c._lifespan:.1f}s"
                    f"  food={c.food_eaten}"
                    f"  social={c.social_interactions}"
                    f"  dist={c.distance_travelled:.0f}px"
                )

        lines.append(sep)
        for line in lines:
            self._emit(line)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _emit(self, line: str) -> None:
        if LOG_TO_CONSOLE:
            print(line, flush=True)
        if LOG_TO_FILE and self._file:
            self._file.write(line + "\n")
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
