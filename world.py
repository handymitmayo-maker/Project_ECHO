# =============================================================================
# PROJECT ECHO – world.py
# Container for all simulation entities.
# Handles biome generation, food spawning, updates, spatial queries, rendering.
# =============================================================================

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

from settings import (
    WORLD_WIDTH, WORLD_HEIGHT,
    CREATURE_COUNT,
    FOOD_INITIAL_COUNT, FOOD_SPAWN_INTERVAL, FOOD_SPAWN_BATCH, FOOD_MAX_COUNT,
    BIOME_COUNT, BIOME_RADIUS_MIN, BIOME_RADIUS_MAX,
    BIOME_FERTILE_COUNT, BIOME_BARREN_COUNT,
    BIOME_FERTILE_RATE, BIOME_NEUTRAL_RATE, BIOME_BARREN_RATE,
    BIOME_CLUSTER_STD, DEBUG_SHOW_BIOMES,
    COLOR_BIOME_FERTILE, COLOR_BIOME_NEUTRAL, COLOR_BIOME_BARREN,
    COLOR_BG, SCANLINE_ALPHA, STATS_INTERVAL,
)
from creature import Creature
from food import Food
from logger import get_logger


# =============================================================================
@dataclass
class Biome:
    """
    An invisible ecological region that concentrates food spawning.

    Attributes
    ----------
    center  : world-space position
    radius  : visual/logical radius (used only for debug overlay)
    type    : "fertile" | "neutral" | "barren"
    rate    : spawn weight (higher = more food)
    color   : debug overlay fill color
    """
    center : pygame.Vector2
    radius : float
    type   : str
    rate   : float
    color  : tuple


# =============================================================================
class World:
    """
    Top-level simulation container.

    Attributes
    ----------
    creatures   : active Creature list (alive + corpses)
    foods       : active Food list
    biomes      : ecological regions controlling food distribution

    Extension placeholders
    ----------------------
    tile_map    : future TileMap instance
    ui_layer    : future HUD/overlay renderer
    tick        : simulation step counter
    """

    def __init__(self) -> None:
        self.creatures : list[Creature] = []
        self.foods     : list[Food]     = []
        self.biomes    : list[Biome]    = self._generate_biomes()

        # Internal timers
        self._food_timer  = 0.0
        self._stats_timer = 0.0

        # Scanline + biome overlay surfaces (built once, reused)
        self._scanline_surf : pygame.Surface | None = None
        self._biome_surf    : pygame.Surface | None = None

        # Extension placeholders
        self.tile_map  = None
        self.ui_layer  = None
        self.tick      = 0

        self._spawn_initial_entities()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _generate_biomes(self) -> list[Biome]:
        """
        Place BIOME_COUNT biomes spread across the map.
        Fertile biomes come first, barren last, rest are neutral.
        A minimum distance check prevents tight clumping.
        """
        biome_types = (
            ["fertile"] * BIOME_FERTILE_COUNT
            + ["barren"]  * BIOME_BARREN_COUNT
            + ["neutral"] * (BIOME_COUNT - BIOME_FERTILE_COUNT - BIOME_BARREN_COUNT)
        )
        rate_map  = {"fertile": BIOME_FERTILE_RATE,
                     "neutral": BIOME_NEUTRAL_RATE,
                     "barren":  BIOME_BARREN_RATE}
        color_map = {"fertile": COLOR_BIOME_FERTILE,
                     "neutral": COLOR_BIOME_NEUTRAL,
                     "barren":  COLOR_BIOME_BARREN}

        biomes : list[Biome] = []
        min_sep = BIOME_RADIUS_MIN * 1.6   # minimum center-to-center distance

        for btype in biome_types:
            for _ in range(200):           # max attempts before giving up
                cx = random.uniform(BIOME_RADIUS_MIN, WORLD_WIDTH  - BIOME_RADIUS_MIN)
                cy = random.uniform(BIOME_RADIUS_MIN, WORLD_HEIGHT - BIOME_RADIUS_MIN)
                pos = pygame.Vector2(cx, cy)

                # Accept if far enough from every existing biome
                if all(pos.distance_to(b.center) >= min_sep for b in biomes):
                    r = random.uniform(BIOME_RADIUS_MIN, BIOME_RADIUS_MAX)
                    biomes.append(Biome(
                        center=pos,
                        radius=r,
                        type=btype,
                        rate=rate_map[btype],
                        color=color_map[btype],
                    ))
                    break

        return biomes

    def _spawn_initial_entities(self) -> None:
        """Populate world with starting creatures and biome-distributed food."""
        for _ in range(CREATURE_COUNT):
            self.creatures.append(self._make_creature())
        for _ in range(FOOD_INITIAL_COUNT):
            biome = self._pick_biome()
            self.foods.append(self._make_food_at_biome(biome))

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """Advance simulation by dt seconds."""
        self.tick += 1

        # Update creatures: alive ones run full AI; dead ones advance corpse fade
        for creature in self.creatures:
            if creature.alive:
                creature.update(self, dt)
            elif creature.is_corpse:
                creature.update_corpse(dt)

        # Remove corpses whose fade timer has expired
        self.creatures = [c for c in self.creatures if c.alive or c.is_corpse]

        # Update food animations
        for food in self.foods:
            food.update(dt)

        # Remove consumed food
        self.foods = [f for f in self.foods if f.alive]

        # Periodically spawn new food (biome-weighted)
        self._food_timer += dt
        if self._food_timer >= FOOD_SPAWN_INTERVAL:
            self._food_timer = 0.0
            self._spawn_food_batch()

        # Periodic statistics dump
        self._stats_timer += dt
        if self._stats_timer >= STATS_INTERVAL:
            self._stats_timer = 0.0
            get_logger().log_stats(self)

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        """Render the entire world to surface."""
        surface.fill(COLOR_BG)

        if DEBUG_SHOW_BIOMES:
            self._draw_biomes(surface)

        for food in self.foods:
            food.draw(surface)

        # Corpses render first (underneath living creatures)
        for creature in self.creatures:
            if creature.is_corpse:
                creature.draw(surface)

        # Living creatures render on top
        for creature in self.creatures:
            if creature.alive:
                creature.draw(surface)

        self._draw_scanlines(surface)

    # ------------------------------------------------------------------
    # Spatial queries (used by Creature AI)
    # ------------------------------------------------------------------

    def get_nearest_food(self, pos: pygame.Vector2) -> Food | None:
        """Return the closest alive Food to pos (global scan). Used as last resort."""
        best      = None
        best_dist = float("inf")
        for food in self.foods:
            d = pos.distance_squared_to(food.pos)
            if d < best_dist:
                best_dist = d
                best      = food
        return best

    def get_nearest_food_in_radius(
        self, pos: pygame.Vector2, radius: float
    ) -> Food | None:
        """Return the closest alive Food within radius, or None if none visible."""
        r2        = radius * radius
        best      = None
        best_dist = float("inf")
        for food in self.foods:
            d = pos.distance_squared_to(food.pos)
            if d <= r2 and d < best_dist:
                best_dist = d
                best      = food
        return best

    def get_nearby_creatures(
        self,
        pos     : pygame.Vector2,
        radius  : float,
        exclude : Creature | None = None,
    ) -> list[Creature]:
        """Return all alive (non-corpse) creatures within radius of pos."""
        r2      = radius * radius
        result  = []
        for c in self.creatures:
            if c is exclude:
                continue
            if not c.alive:
                continue
            if pos.distance_squared_to(c.pos) <= r2:
                result.append(c)
        return result

    # ------------------------------------------------------------------
    # Spawning helpers
    # ------------------------------------------------------------------

    def _pick_biome(self) -> Biome:
        """Weighted-random biome selection by spawn rate."""
        weights = [b.rate for b in self.biomes]
        return random.choices(self.biomes, weights=weights, k=1)[0]

    def _spawn_food_batch(self) -> None:
        """Spawn up to FOOD_SPAWN_BATCH items, each placed in a weighted-random biome."""
        available = FOOD_MAX_COUNT - len(self.foods)
        count     = min(FOOD_SPAWN_BATCH, available)
        for _ in range(count):
            biome = self._pick_biome()
            self.foods.append(self._make_food_at_biome(biome))

    def _make_food_at_biome(self, biome: Biome) -> Food:
        """Place a food item near biome center using Gaussian scatter."""
        angle = random.uniform(0, math.tau)
        dist  = abs(random.gauss(0, BIOME_CLUSTER_STD))
        x     = biome.center.x + math.cos(angle) * dist
        y     = biome.center.y + math.sin(angle) * dist
        x     = max(10, min(WORLD_WIDTH  - 10, x))
        y     = max(10, min(WORLD_HEIGHT - 10, y))
        return Food(x, y)

    @staticmethod
    def _make_creature() -> Creature:
        return Creature(
            x=random.uniform(20, WORLD_WIDTH  - 20),
            y=random.uniform(20, WORLD_HEIGHT - 20),
        )

    # ------------------------------------------------------------------
    # Visual effects
    # ------------------------------------------------------------------

    def _draw_biomes(self, surface: pygame.Surface) -> None:
        """Draw semi-transparent biome circles (debug overlay, built once)."""
        if self._biome_surf is None:
            self._biome_surf = pygame.Surface(
                (WORLD_WIDTH, WORLD_HEIGHT), pygame.SRCALPHA
            )
            for biome in self.biomes:
                pygame.draw.circle(
                    self._biome_surf,
                    (*biome.color, 35),
                    (int(biome.center.x), int(biome.center.y)),
                    int(biome.radius),
                )
        surface.blit(self._biome_surf, (0, 0))

    def _draw_scanlines(self, surface: pygame.Surface) -> None:
        """Overlay a subtle scanline pattern for retro atmosphere."""
        if SCANLINE_ALPHA == 0:
            return

        w, h = surface.get_size()
        if self._scanline_surf is None or self._scanline_surf.get_size() != (w, h):
            self._scanline_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            for y in range(0, h, 4):
                pygame.draw.line(
                    self._scanline_surf,
                    (0, 0, 0, SCANLINE_ALPHA),
                    (0, y),
                    (w, y),
                )
        surface.blit(self._scanline_surf, (0, 0))

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"World(creatures={len(self.creatures)}, "
            f"foods={len(self.foods)}, "
            f"biomes={len(self.biomes)}, "
            f"tick={self.tick})"
        )
