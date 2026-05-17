# =============================================================================
# PROJECT ECHO – verify_seed.py
# Automated check: identical WORLD HASH across repeated World() builds.
# =============================================================================

from __future__ import annotations

import sys


def main() -> int:
    import pygame
    pygame.init()

    import settings
    settings.USE_FIXED_SEED = True
    settings.WORLD_SEED = 1337

    from world_seed import reseed_world_rng
    from world import World

    reseed_world_rng()
    world_a = World()
    hash_a = world_a.initial_hash

    reseed_world_rng()
    world_b = World()
    hash_b = world_b.initial_hash

    if hash_a != hash_b:
        print(f"FAIL: hashes differ  {hash_a}  vs  {hash_b}")
        return 1

    print(f"PASS: WORLD HASH {hash_a} (stable across 2 builds)")
    print(f"  biomes={len(world_a.biomes)}  creatures={len(world_a.creatures)}  food={len(world_a.foods)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
