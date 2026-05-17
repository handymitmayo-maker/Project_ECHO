# =============================================================================
# PROJECT ECHO – simulation_hash.py
# Canonical fingerprint of initial world layout for seed verification.
# =============================================================================

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from world import World


def _round2(v: float) -> float:
    return round(v, 2)


def hash_payload(world: "World") -> dict[str, Any]:
    """
    Build a stable JSON-serializable snapshot of world-start layout.
    Excludes runtime state and creature UUIDs.
    """
    biomes = sorted(
        [
            {
                "type": b.type,
                "x": _round2(b.center.x),
                "y": _round2(b.center.y),
                "r": _round2(b.radius),
            }
            for b in world.biomes
        ],
        key=lambda x: (x["type"], x["x"], x["y"]),
    )

    creatures = []
    for c in sorted(world.creatures, key=lambda x: x.label):
        creatures.append({
            "label": c.label,
            "x": _round2(c.pos.x),
            "y": _round2(c.pos.y),
            "risk": _round2(c.risk_tolerance),
            "lazy": _round2(c.laziness),
            "social_dep": _round2(c.social_dependency),
            "greed": _round2(c.food_greed),
            "speed": _round2(c._speed),
            "hunger": _round2(c.hunger),
            "energy": _round2(c.energy),
            "social": _round2(c.social),
            "wander_angle": _round2(c._wander_angle),
        })

    foods = sorted(
        [
            {"x": _round2(f.pos.x), "y": _round2(f.pos.y)}
            for f in world.foods
        ],
        key=lambda x: (x["x"], x["y"]),
    )

    return {"biomes": biomes, "creatures": creatures, "foods": foods}


def compute_world_hash(world: "World") -> str:
    """Return a short hex fingerprint, e.g. 'A91F-22C7'."""
    payload = hash_payload(world)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8].upper()
    return f"{digest[:4]}-{digest[4:]}"
