# =============================================================================
# PROJECT ECHO – debug_controls.py
# Central runtime toggles for all debug/visualization options.
# =============================================================================

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import pygame

import settings

if TYPE_CHECKING:
    from world import World


# (settings attribute, key name, short label, needs biome overlay rebuild)
_TOGGLE_SPECS: list[tuple[str, str, str, bool]] = [
    ("DEBUG_MODE",            "D", "Debug HUD",       False),
    ("DEBUG_SHOW_BIOMES",     "B", "Biome zones",     True),
    ("BIOME_SHOW_LABELS",     "N", "Biome labels",    True),
    ("DEBUG_SHOW_PERCEPTION", "P", "Perception",      False),
    ("SHOW_CREATURE_LABELS",  "L", "Creature labels", False),
    ("SHOW_STATUS_BARS",      "V", "Status bars",     False),
    ("DEBUG_SHOW_BOND_LINES", "G", "Bond lines",      False),
    ("DEBUG_SHOW_LINEAGE_TINT", "T", "Lineage tint",  False),
]

_KEY_MAP: dict[int, str] = {
    getattr(pygame, f"K_{key.lower()}"): attr
    for attr, key, _, _ in _TOGGLE_SPECS
}


def is_on(attr: str) -> bool:
    return bool(getattr(settings, attr, False))


def toggle(attr: str, world: "World | None" = None) -> None:
    """Flip a debug flag; rebuild biome overlay when needed."""
    setattr(settings, attr, not is_on(attr))
    if world is None:
        return
    rebuild = any(
        spec[0] == attr and spec[3]
        for spec in _TOGGLE_SPECS
    )
    if not rebuild:
        return
    if settings.DEBUG_SHOW_BIOMES:
        world._rebuild_biome_overlay()
    else:
        world._biome_surf = None


def handle_key(key: int, world: "World | None" = None) -> bool:
    """Handle a debug toggle key. Returns True if consumed."""
    attr = _KEY_MAP.get(key)
    if attr is None:
        return False
    toggle(attr, world)
    return True


def status_lines() -> list[str]:
    """HUD lines showing each toggle and its key."""
    return [
        f"[{key}] {label:<16} {'ON' if is_on(attr) else 'off'}"
        for attr, key, label, _ in _TOGGLE_SPECS
    ]


def dump_rng(world: "World | None" = None) -> None:
    """Log current RNG / world hash state ([H])."""
    from world_seed import dump_rng_status
    from logger import get_logger

    wh = world.initial_hash if world is not None else None
    log = get_logger()
    for line in dump_rng_status(wh):
        log.log_event("RNG_DUMP", line, "SYSTEM")


def help_lines() -> list[str]:
    """Full control reference for the help overlay."""
    lines = ["--- DEBUG CONTROLS ---"]
    lines.extend(status_lines())
    lines.append("--- OBSERVER ---")
    lines.append("[Click] Select creature")
    lines.append("[F]   Freeze simulation")
    lines.append("[I]   Dump creature profile")
    lines.append("[H]   RNG / world hash dump")
    lines.append("[?] Help overlay")
    lines.append("[SPACE] Spawn food")
    lines.append("[ESC] Quit")
    return lines
