# =============================================================================
# PROJECT ECHO – world.py
# Container for all simulation entities.
# Handles spawning, updates, spatial queries, and rendering.
# =============================================================================

from __future__ import annotations

import random

import pygame

from settings import (
    WORLD_WIDTH, WORLD_HEIGHT,
    CREATURE_COUNT,
    FOOD_INITIAL_COUNT, FOOD_SPAWN_INTERVAL, FOOD_SPAWN_BATCH, FOOD_MAX_COUNT,
    COLOR_BG, SCANLINE_ALPHA, STATS_INTERVAL,
)
from creature import Creature
from food import Food
from logger import get_logger


class World:
    """
    Top-level simulation container.

    Attributes
    ----------
    creatures   : active Creature list
    foods       : active Food list

    Extension placeholders
    ----------------------
    tile_map    : future Tilemap object
    ui_layer    : future HUD/overlay renderer
    tick        : simulation step counter (useful for scripted events)
    """

    def __init__(self) -> None:
        self.creatures : list[Creature] = []
        self.foods     : list[Food]     = []

        # Internal timers
        self._food_timer  = 0.0
        self._stats_timer = 0.0

        # Scanline overlay surface (created once, reused every frame)
        self._scanline_surf : pygame.Surface | None = None

        # Extension placeholders
        self.tile_map  = None   # future: TileMap instance
        self.ui_layer  = None   # future: UILayer instance
        self.tick      = 0      # simulation step counter

        self._spawn_initial_entities()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _spawn_initial_entities(self) -> None:
        """Populate world with starting creatures and food."""
        for _ in range(CREATURE_COUNT):
            self.creatures.append(self._make_creature())
        for _ in range(FOOD_INITIAL_COUNT):
            self.foods.append(self._make_food())

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """Advance simulation by dt seconds."""
        self.tick += 1

        # Update all creatures
        for creature in self.creatures:
            creature.update(self, dt)

        # Update food animations
        for food in self.foods:
            food.update(dt)

        # Remove consumed food
        self.foods = [f for f in self.foods if f.alive]

        # Periodically spawn new food
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

        for food in self.foods:
            food.draw(surface)

        for creature in self.creatures:
            creature.draw(surface)

        self._draw_scanlines(surface)

        # Extension: self.ui_layer.draw(surface) when implemented

    # ------------------------------------------------------------------
    # Spatial queries (used by Creature AI)
    # ------------------------------------------------------------------

    def get_nearest_food(self, pos: pygame.Vector2) -> Food | None:
        """Return the closest alive Food to pos, or None if none exist."""
        best      = None
        best_dist = float("inf")
        for food in self.foods:
            d = pos.distance_squared_to(food.pos)
            if d < best_dist:
                best_dist = d
                best      = food
        return best

    def get_nearby_creatures(
        self,
        pos     : pygame.Vector2,
        radius  : float,
        exclude : Creature | None = None,
    ) -> list[Creature]:
        """Return all creatures within radius of pos, optionally excluding one."""
        r2      = radius * radius
        result  = []
        for c in self.creatures:
            if c is exclude:
                continue
            if pos.distance_squared_to(c.pos) <= r2:
                result.append(c)
        return result

    # ------------------------------------------------------------------
    # Spawning helpers
    # ------------------------------------------------------------------

    def _spawn_food_batch(self) -> None:
        """Spawn up to FOOD_SPAWN_BATCH new food items if under the cap."""
        available = FOOD_MAX_COUNT - len(self.foods)
        count     = min(FOOD_SPAWN_BATCH, available)
        for _ in range(count):
            self.foods.append(self._make_food())

    @staticmethod
    def _make_creature() -> Creature:
        return Creature(
            x=random.uniform(20, WORLD_WIDTH  - 20),
            y=random.uniform(20, WORLD_HEIGHT - 20),
        )

    @staticmethod
    def _make_food() -> Food:
        return Food(
            x=random.uniform(10, WORLD_WIDTH  - 10),
            y=random.uniform(10, WORLD_HEIGHT - 10),
        )

    # ------------------------------------------------------------------
    # Visual effects
    # ------------------------------------------------------------------

    def _draw_scanlines(self, surface: pygame.Surface) -> None:
        """Overlay a subtle scanline pattern for retro atmosphere."""
        if SCANLINE_ALPHA == 0:
            return

        w, h = surface.get_size()

        # Build the scanline surface only once (or if window resized)
        if self._scanline_surf is None or self._scanline_surf.get_size() != (w, h):
            self._scanline_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            for y in range(0, h, 4):          # every 4th row
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
            f"tick={self.tick})"
        )
