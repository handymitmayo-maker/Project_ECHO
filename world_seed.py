# =============================================================================
# PROJECT ECHO – world_seed.py
# Deterministic world initialization for reproducible research runs.
# =============================================================================

from __future__ import annotations

import random

import settings


_active_seed: int | None = None
_mode: str = "CHAOS"


def init_world_seed() -> None:
    """
    Seed Python's global random module before world / creature generation.

    RESEARCH (USE_FIXED_SEED=True):
        Identical biomes, spawns, traits, and food layout each run.
        Creature labels reset so ECHO-01..N match across sessions.

    CHAOS (USE_FIXED_SEED=False):
        No fixed seed; each session draws from OS entropy.
    """
    global _active_seed, _mode

    from creature import Creature

    if settings.USE_FIXED_SEED:
        _active_seed = int(settings.WORLD_SEED)
        _mode = "RESEARCH"
        random.seed(_active_seed)
    else:
        _active_seed = None
        _mode = "CHAOS"

    Creature.reset_label_counter()


def reseed_world_rng() -> None:
    """
    Re-apply the world seed immediately before World() construction.

    Boot UI and other pre-world code must not advance the global RNG used
    for biomes, spawns, and initial food layout.
    """
    global _active_seed, _mode

    from creature import Creature

    if settings.USE_FIXED_SEED:
        _active_seed = int(settings.WORLD_SEED)
        _mode = "RESEARCH"
        random.seed(_active_seed)
    else:
        _active_seed = None
        _mode = "CHAOS"

    Creature.reset_label_counter()


def get_mode() -> str:
    """RESEARCH or CHAOS."""
    return _mode


def get_active_seed() -> int | None:
    """Numeric seed when fixed; None in chaos mode."""
    return _active_seed


def seed_display() -> str:
    """Human-readable seed for logs and boot UI."""
    if _active_seed is not None:
        return str(_active_seed)
    return "RANDOM"


def boot_sidebar_seed() -> str:
    """Seed string shown on the boot screen metadata panel."""
    if _active_seed is not None:
        return str(_active_seed)
    return "RANDOM"


def dump_rng_status(world_hash: str | None = None) -> list[str]:
    """Lines for logger/console RNG diagnostic dump."""
    state = random.getstate()
    internal = state[1]
    lines = [
        f"mode={get_mode()}  seed={seed_display()}  active={_active_seed}",
        f"rng_state[0]={internal[0] if internal else 'n/a'}",
        f"rng_state_len={len(internal)}",
    ]
    if world_hash is not None:
        lines.insert(1, f"world_hash={world_hash}")
    return lines
