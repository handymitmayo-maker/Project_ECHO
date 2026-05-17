# =============================================================================
# PROJECT ECHO – lineage_utils.py
# Lineage resolution, profile formatting, and visual tint helpers.
# =============================================================================

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from settings import (
    PARTNER_NEST_DISTANCE,
    REPRO_AGE_MIN,
    REPRO_ENERGY_MIN,
    REPRO_HUNGER_MAX,
    COLOR_CREATURE,
)

if TYPE_CHECKING:
    from creature import Creature
    from world import World


def resolve_parents(creature: "Creature", world: "World") -> tuple["Creature | None", "Creature | None"]:
    pa = world.get_creature_by_id(creature.parent_a_id) if creature.parent_a_id else None
    pb = world.get_creature_by_id(creature.parent_b_id) if creature.parent_b_id else None
    return pa, pb


def count_offspring(creature: "Creature", world: "World") -> int:
    n = 0
    cid = creature.id
    for c in world.creatures:
        if c.parent_a_id == cid or c.parent_b_id == cid:
            n += 1
    return n


def best_friend(creature: "Creature") -> tuple[str, float]:
    if not creature.relationships:
        return "none", 0.0
    best_id = max(creature.relationships, key=lambda k: creature.relationships[k]["affinity"])
    entry = creature.relationships[best_id]
    if entry["affinity"] <= 0:
        return "none", 0.0
    return entry["label"], entry["affinity"]


def strongest_affinity(creature: "Creature") -> tuple[str, float]:
    return best_friend(creature)


def lineage_members(world: "World", lineage_id: uuid.UUID) -> list["Creature"]:
    return [c for c in world.creatures if c.lineage_id == lineage_id]


def lineage_tint(lineage_id: uuid.UUID) -> tuple[int, int, int]:
    """Stable subtle tint from lineage id (founders stay near base green)."""
    data = lineage_id.bytes
    shift = ((data[0] + data[1] + data[2]) % 31) - 15
    r, g, b = COLOR_CREATURE
    return (
        max(0, min(255, r + shift // 2)),
        max(0, min(255, g + shift)),
        max(0, min(255, b + shift // 3)),
    )


def _target_label(creature: "Creature") -> str:
    if creature.target is None:
        return "none"
    if hasattr(creature.target, "label"):
        return creature.target.label
    return "?"


def _life_status(creature: "Creature") -> str:
    if creature.alive:
        return "alive"
    if creature.is_corpse:
        return "corpse"
    return "dead"


def _repro_viability(creature: "Creature", world: "World") -> tuple[bool, str]:
    if not creature.is_reproduction_viable():
        if not creature.alive:
            return False, "not alive"
        if creature.repro_cooldown > 0:
            return False, f"cooldown {creature.repro_cooldown:.0f}s"
        if creature._lifespan < REPRO_AGE_MIN:
            return False, f"age < {REPRO_AGE_MIN:.0f}s"
        if creature.energy < REPRO_ENERGY_MIN:
            return False, f"energy < {REPRO_ENERGY_MIN:.0f}"
        if creature.hunger > REPRO_HUNGER_MAX:
            return False, f"hunger > {REPRO_HUNGER_MAX:.0f}"
        return False, "survival gates"

    partner = creature._get_bonded_partner(world)
    if partner is None:
        return False, "no bonded partner"
    if not creature.is_bonded_with(partner):
        return False, "affinity < bond threshold"
    dist = creature.pos.distance_to(partner.pos)
    if dist > PARTNER_NEST_DISTANCE:
        return False, f"partner {dist:.0f}px away"
    if not partner.is_reproduction_viable():
        return False, "partner not viable"
    return True, "ready"


def format_creature_profile(creature: "Creature", world: "World") -> list[str]:
    """Multi-line profile for inspector panel and logger dump."""
    bf_label, bf_aff = best_friend(creature)
    sf_label, sf_aff = strongest_affinity(creature)
    pa, pb = resolve_parents(creature, world)
    children = count_offspring(creature, world)
    partner = creature._get_bonded_partner(world)
    viable, viable_reason = _repro_viability(creature, world)

    lines = [
        "--- IDENTITY ---",
        f"label     : {creature.display_label()}",
        f"generation: {creature.generation}",
        f"lineage   : {str(creature.lineage_id)[:8]}",
        f"age       : {creature._lifespan:.1f}s",
        f"status    : {_life_status(creature)}",
    ]
    if creature._cause_of_death:
        lines.append(f"cause     : {creature._cause_of_death}")

    lines.extend([
        "--- PERSONALITY ---",
        f"risk      : {creature.risk_tolerance:.2f}",
        f"social    : {creature.social_dependency:.2f}",
        f"greed     : {creature.food_greed:.2f}",
        f"lazy      : {creature.laziness:.2f}",
        f"speed     : {creature._speed:.1f}",
        "--- VITALS ---",
        f"hunger    : {creature.hunger:.1f}",
        f"energy    : {creature.energy:.1f}",
        f"social    : {creature.social:.1f}",
        "--- SOCIAL ---",
        f"partner   : {partner.label if partner else 'none'}",
        f"best frnd : {bf_label} ({bf_aff:.1f})",
        f"top aff   : {sf_label} ({sf_aff:.1f})",
        f"offspring : {creature.offspring_count} born / {children} in world",
        "--- SURVIVAL ---",
        f"meals     : {creature.food_eaten}",
        f"distance  : {creature.distance_travelled:.0f} px",
        f"state     : {creature.state.name}",
        f"target    : {_target_label(creature)}",
        f"repro     : {'yes' if viable else 'no'} ({viable_reason})",
        "--- FAMILY ---",
        f"parent A  : {pa.label if pa else 'unknown'}",
        f"parent B  : {pb.label if pb else 'unknown'}",
        f"children  : {children}",
    ])
    return lines
