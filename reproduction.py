# =============================================================================
# PROJECT ECHO – reproduction.py
# Pair-only reproduction: two living parents, affinity gates, inherited traits.
# =============================================================================

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import pygame

from settings import (
    WORLD_WIDTH, WORLD_HEIGHT,
    MAX_POPULATION,
    BOND_PARTNER_AFFINITY,
    REPRO_AFFINITY_MIN, REPRO_DISTANCE_MAX,
    REPRO_COST_ENERGY, REPRO_COST_HUNGER,
    REPRO_COOLDOWN, REPRO_PAIR_COOLDOWN,
    REPRO_CHECK_INTERVAL, REPRO_CHANCE_BASE, REPRO_BOND_BONUS,
    REPRO_BONDED_AFFINITY, REPRO_BONDED_CHANCE,
    REPRO_SPAWN_OFFSET,
    REL_FRIEND_THRESHOLD,
)
from creature import Creature
from logger import get_logger

if TYPE_CHECKING:
    from world import World


_total_births: int = 0


def update(world: "World", dt: float) -> None:
    """
    Interval-based pair scan. At most one offspring per check cycle.
  """
    world._repro_timer += dt
    if world._repro_timer < REPRO_CHECK_INTERVAL:
        return
    world._repro_timer = 0.0

    for k in list(world._pair_cooldowns):
        world._pair_cooldowns[k] -= dt
        if world._pair_cooldowns[k] <= 0:
            del world._pair_cooldowns[k]

    if world.alive_count() >= MAX_POPULATION:
        return

    alive = [c for c in world.creatures if c.alive]
    for i, a in enumerate(alive):
        for b in alive[i + 1:]:
            if world.alive_count() >= MAX_POPULATION:
                return
            child = _attempt_pair(a, b, world)
            if child is not None:
                return


def _mutual_affinity(a: Creature, b: Creature) -> tuple[float, float]:
    return a.get_affinity_to(b), b.get_affinity_to(a)


def _pair_can_reproduce(a: Creature, b: Creature, world: "World") -> bool:
    if a.id == b.id:
        return False
    if not a.is_reproduction_viable() or not b.is_reproduction_viable():
        return False

    if not a.is_bonded_with(b):
        return False

    aff_ab, aff_ba = _mutual_affinity(a, b)
    if aff_ab < BOND_PARTNER_AFFINITY or aff_ba < BOND_PARTNER_AFFINITY:
        return False
    if aff_ab < REPRO_AFFINITY_MIN or aff_ba < REPRO_AFFINITY_MIN:
        return False

    if a.pos.distance_to(b.pos) > REPRO_DISTANCE_MAX:
        return False

    pair_key = frozenset((a.id, b.id))
    if pair_key in world._pair_cooldowns:
        return False

    if world.alive_count() >= MAX_POPULATION:
        return False

    return True


def _reproduction_chance(a: Creature, b: Creature) -> float:
    aff_ab, aff_ba = _mutual_affinity(a, b)
    avg = (aff_ab + aff_ba) / 2.0
    if avg >= REPRO_BONDED_AFFINITY:
        chance = REPRO_BONDED_CHANCE
    else:
        chance = REPRO_CHANCE_BASE * min(1.0, avg / REPRO_AFFINITY_MIN)
    if aff_ab >= REL_FRIEND_THRESHOLD and aff_ba >= REL_FRIEND_THRESHOLD:
        chance += REPRO_BOND_BONUS
    return min(0.65, chance)


def _spawn_position(a: Creature, b: Creature) -> tuple[float, float]:
    mid_x = (a.pos.x + b.pos.x) / 2.0
    mid_y = (a.pos.y + b.pos.y) / 2.0
    x = mid_x + random.uniform(-REPRO_SPAWN_OFFSET, REPRO_SPAWN_OFFSET)
    y = mid_y + random.uniform(-REPRO_SPAWN_OFFSET, REPRO_SPAWN_OFFSET)
    x = max(20.0, min(WORLD_WIDTH  - 20.0, x))
    y = max(20.0, min(WORLD_HEIGHT - 20.0, y))
    return x, y


def _attempt_pair(a: Creature, b: Creature, world: "World") -> Creature | None:
    if not _pair_can_reproduce(a, b, world):
        return None

    aff_ab, aff_ba = _mutual_affinity(a, b)
    dist = a.pos.distance_to(b.pos)
    log = get_logger()
    log.log_event(
        "REPRODUCTION_ATTEMPT",
        (
            f"{a.label} + {b.label}  "
            f"affinity={aff_ab:.1f}/{aff_ba:.1f}  dist={dist:.0f}px"
        ),
        a.label,
    )

    if random.random() > _reproduction_chance(a, b):
        return None

    x, y = _spawn_position(a, b)
    child = Creature.create_offspring(a, b, x, y)
    world.creatures.append(child)

    # Parent costs
    a.energy = max(0.0, a.energy - REPRO_COST_ENERGY)
    b.energy = max(0.0, b.energy - REPRO_COST_ENERGY)
    a.hunger = min(100.0, a.hunger + REPRO_COST_HUNGER)
    b.hunger = min(100.0, b.hunger + REPRO_COST_HUNGER)

    a.repro_cooldown = REPRO_COOLDOWN
    b.repro_cooldown = REPRO_COOLDOWN
    a.offspring_count += 1
    b.offspring_count += 1

    pair_key = frozenset((a.id, b.id))
    world._pair_cooldowns[pair_key] = REPRO_PAIR_COOLDOWN

    log.log_reproduction(a, b, child)
    log.log_event(
        "REPRODUCTION_SUCCESS",
        (
            f"{a.label} + {b.label} -> {child.label}  "
            f"GEN-{child.generation}"
        ),
        child.label,
    )
    log.log_offspring_born(child)
    log.log_family_line(child)

    global _total_births
    _total_births += 1

    return child


def generation_stats(world: "World") -> dict:
    """Snapshot for periodic GENERATION_STATS logging."""
    alive = [c for c in world.creatures if c.alive]
    if not alive:
        return {"max_gen": 0, "avg_gen": 0.0, "births": _total_births}
    gens = [c.generation for c in alive]
    return {
        "max_gen": max(gens),
        "avg_gen": sum(gens) / len(gens),
        "births": _total_births,
    }


def reset_session_counters() -> None:
    global _total_births
    _total_births = 0
