# =============================================================================
# PROJECT ECHO – creature.py
# Autonomous agent with a simple state-machine AI.
# =============================================================================

from __future__ import annotations

import math
import random
import uuid
from enum import Enum, auto
from typing import TYPE_CHECKING

import pygame

from settings import (
    CREATURE_RADIUS, CREATURE_SPEED, CREATURE_SPEED_MIN, CREATURE_SPEED_MAX,
    CREATURE_ARRIVE_RADIUS, CREATURE_ACCEL_FACTOR, CREATURE_FRICTION,
    HUNGER_DECAY_RATE, ENERGY_DECAY_RATE, ENERGY_REST_RATE,
    SOCIAL_DECAY_RATE, SOCIAL_GAIN_RATE,
    HUNGER_THRESHOLD, ENERGY_THRESHOLD, SOCIAL_THRESHOLD,
    WANDER_CHANGE_INTERVAL, WANDER_CIRCLE_DIST, WANDER_CIRCLE_RADIUS,
    WANDER_ANGLE_SPEED, SOCIAL_RADIUS,
    IDLE_CHANCE, IDLE_DURATION_MIN, IDLE_DURATION_MAX,
    WORLD_WIDTH, WORLD_HEIGHT,
    COLOR_CREATURE, COLOR_CREATURE_REST, COLOR_CREATURE_SOCIAL,
    COLOR_CREATURE_SEEK,
    COLOR_BAR_BG, COLOR_BAR_HUNGER, COLOR_BAR_ENERGY, COLOR_BAR_SOCIAL,
    SHOW_STATUS_BARS, BAR_WIDTH, BAR_HEIGHT, BAR_SPACING,
)

if TYPE_CHECKING:
    from world import World


# =============================================================================
class State(Enum):
    WANDER     = auto()
    SEEK_FOOD  = auto()
    REST       = auto()
    SOCIALIZE  = auto()


# Colour per state
_STATE_COLOR = {
    State.WANDER:    COLOR_CREATURE,
    State.SEEK_FOOD: COLOR_CREATURE_SEEK,
    State.REST:      COLOR_CREATURE_REST,
    State.SOCIALIZE: COLOR_CREATURE_SOCIAL,
}


# =============================================================================
class Creature:
    """
    A single autonomous creature.

    Drives itself via a priority-based state machine:
        SEEK_FOOD  (highest priority – survival)
        REST
        SOCIALIZE
        WANDER     (default / fallback)

    Extension hooks (populated in future versions):
        self.memory        – episodic memory list
        self.dna           – heritable trait dict
        self.relationships – {creature_id: affinity_float}
    """

    def __init__(self, x: float, y: float) -> None:
        self.id            = uuid.uuid4()
        self.pos           = pygame.Vector2(x, y)
        self.vel           = pygame.Vector2(
            random.uniform(-1, 1), random.uniform(-1, 1)
        ).normalize() * random.uniform(CREATURE_SPEED_MIN * 0.3, CREATURE_SPEED_MIN * 0.7)

        # --- Personality ---
        self._speed        = random.uniform(CREATURE_SPEED_MIN, CREATURE_SPEED_MAX)

        # --- Vital stats (0–100) ---
        self.hunger  = random.uniform(20, 60)   # grows over time; high = hungry
        self.energy  = random.uniform(50, 100)
        self.social  = random.uniform(30, 90)

        # --- State machine ---
        self.state   = State.WANDER
        self.target  = None                      # Food object or Vector2

        # Wander / Reynolds wander circle
        self._wander_timer  = 0.0
        self._wander_angle  = random.uniform(0, math.tau)   # current wander heading angle

        # Idle sub-state
        self._is_idle       = False
        self._idle_timer    = 0.0
        self._idle_duration = 0.0

        # --- Extension placeholders ---
        self.memory        : list        = []    # future: episodic events
        self.dna           : dict        = {}    # future: heritable traits
        self.relationships : dict        = {}    # future: {id: affinity}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, world: "World", dt: float) -> None:
        """Main update: decide state, then act."""
        self._decay_stats(dt)
        self._decide_state(world)
        self._act(world, dt)
        self._move(dt)
        self._wrap_borders()

    def draw(self, surface: pygame.Surface) -> None:
        """Render creature and optional status bars."""
        px, py = int(self.pos.x), int(self.pos.y)
        color  = _STATE_COLOR[self.state]

        # Glow aura
        glow_r = CREATURE_RADIUS + 5
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(
            glow_surf,
            (*color, 40),
            (glow_r, glow_r),
            glow_r,
        )
        surface.blit(glow_surf, (px - glow_r, py - glow_r))

        # Core body
        pygame.draw.circle(surface, color, (px, py), CREATURE_RADIUS)

        if SHOW_STATUS_BARS:
            self._draw_status_bars(surface, px, py)

    # ------------------------------------------------------------------
    # Private – AI
    # ------------------------------------------------------------------

    def _decide_state(self, world: "World") -> None:
        """Priority-based state selection."""
        if self.hunger >= HUNGER_THRESHOLD:
            self.state  = State.SEEK_FOOD
            nearest     = world.get_nearest_food(self.pos)
            self.target = nearest          # may be None if no food exists
        elif self.energy <= ENERGY_THRESHOLD:
            self.state  = State.REST
            self.target = None
        elif self.social <= SOCIAL_THRESHOLD:
            self.state  = State.SOCIALIZE
            nearby      = world.get_nearby_creatures(self.pos, SOCIAL_RADIUS, exclude=self)
            self.target = nearby[0] if nearby else None
        else:
            self.state  = State.WANDER
            self.target = None

    def _act(self, world: "World", dt: float) -> None:
        """Translate current state into steering forces."""
        if self.state == State.SEEK_FOOD:
            if self.target is not None and self.target.alive:
                self._steer_arrive(self.target.pos)
                if self.pos.distance_to(self.target.pos) < CREATURE_RADIUS + self.target.radius:
                    self._eat(self.target)
            else:
                self._steer_wander(dt)

        elif self.state == State.REST:
            # Gradually stop
            self.vel *= max(0.0, 1.0 - dt * 4)

        elif self.state == State.SOCIALIZE:
            if self.target is not None:
                self._steer_arrive(self.target.pos)
                if self.pos.distance_to(self.target.pos) < SOCIAL_RADIUS * 0.5:
                    self.social = min(100, self.social + SOCIAL_GAIN_RATE * dt)
            else:
                self._steer_wander(dt)

        else:  # WANDER
            self._steer_wander(dt)

    # ------------------------------------------------------------------
    # Private – Steering Behaviors
    # ------------------------------------------------------------------

    def _steer_arrive(self, target_pos: pygame.Vector2) -> None:
        """
        Craig Reynolds 'Arrive' steering behavior.
        Slows down as the creature approaches the target.
        Energy reduces top speed; hunger increases urgency.
        """
        to_target = target_pos - self.pos
        dist      = to_target.length()
        if dist < 0.1:
            return

        # Tired creatures move slower
        energy_factor   = 0.5 + 0.5 * (self.energy / 100)
        effective_speed = self._speed * energy_factor

        # Hungry creatures are faster and steer more sharply
        if self.state == State.SEEK_FOOD:
            effective_speed *= 1.4
            lerp = CREATURE_ACCEL_FACTOR * 1.8
        else:
            lerp = CREATURE_ACCEL_FACTOR

        if dist < CREATURE_ARRIVE_RADIUS:
            effective_speed *= dist / CREATURE_ARRIVE_RADIUS

        desired_vel = to_target.normalize() * effective_speed
        self.vel    = self.vel.lerp(desired_vel, lerp)

    def _steer_wander(self, dt: float) -> None:
        """
        Reynolds Wander Circle steering.
        Projects a circle ahead of the creature and picks a point on it,
        perturbing the angle each frame for organic curved paths.
        Periodically triggers idle pauses where the creature gently stops.
        """
        # --- Idle sub-state ---
        if self._is_idle:
            self._idle_timer += dt
            self.vel *= max(0.0, 1.0 - dt * 5)      # decelerate to a stop
            if self._idle_timer >= self._idle_duration:
                self._is_idle = False
            return

        # --- Periodic idle roll ---
        self._wander_timer += dt
        if self._wander_timer >= WANDER_CHANGE_INTERVAL:
            self._wander_timer = 0.0
            if random.random() < IDLE_CHANCE:
                self._is_idle       = True
                self._idle_timer    = 0.0
                self._idle_duration = random.uniform(IDLE_DURATION_MIN, IDLE_DURATION_MAX)
                return

        # --- Perturb wander angle (organic drift) ---
        self._wander_angle += random.uniform(-WANDER_ANGLE_SPEED, WANDER_ANGLE_SPEED) * dt

        # --- Project wander circle ahead of current heading ---
        if self.vel.length() > 1.0:
            ahead = self.vel.normalize() * WANDER_CIRCLE_DIST
        else:
            ahead = pygame.Vector2(
                math.cos(self._wander_angle),
                math.sin(self._wander_angle),
            ) * WANDER_CIRCLE_DIST

        circle_center = self.pos + ahead
        wander_target = circle_center + pygame.Vector2(
            math.cos(self._wander_angle) * WANDER_CIRCLE_RADIUS,
            math.sin(self._wander_angle) * WANDER_CIRCLE_RADIUS,
        )
        self._steer_arrive(wander_target)

    # ------------------------------------------------------------------
    # Private – Stats
    # ------------------------------------------------------------------

    def _decay_stats(self, dt: float) -> None:
        """Drain stats over time according to current state."""
        self.hunger = min(100, self.hunger + HUNGER_DECAY_RATE * dt)

        if self.state == State.REST:
            self.energy = min(100, self.energy + ENERGY_REST_RATE * dt)
        else:
            self.energy = max(0, self.energy - ENERGY_DECAY_RATE * dt)

        # Social: rises near others (handled in _act), falls alone
        if self.state != State.SOCIALIZE:
            self.social = max(0, self.social - SOCIAL_DECAY_RATE * dt)

    def _eat(self, food) -> None:
        """Consume a food item."""
        self.hunger = max(0, self.hunger - food.nutrition)
        food.alive  = False
        self.target = None
        # Extension: self.memory.append({"event": "ate", "pos": self.pos.copy()})

    # ------------------------------------------------------------------
    # Private – Utilities
    # ------------------------------------------------------------------

    def _move(self, dt: float) -> None:
        """Apply friction, cap velocity, then integrate position."""
        # Natural drag – prevents endless gliding when no steering force is applied
        self.vel *= max(0.0, 1.0 - CREATURE_FRICTION * dt)

        # Per-creature speed cap, reduced when tired
        energy_factor = 0.5 + 0.5 * (self.energy / 100)
        max_speed     = self._speed * energy_factor
        if self.state == State.SEEK_FOOD:
            max_speed *= 1.4

        speed = self.vel.length()
        if speed > max_speed:
            self.vel = self.vel.normalize() * max_speed

        self.pos += self.vel * dt

    def _wrap_borders(self) -> None:
        """Wrap creature position around world edges (toroidal topology)."""
        if self.pos.x < 0:
            self.pos.x = WORLD_WIDTH
        elif self.pos.x > WORLD_WIDTH:
            self.pos.x = 0
        if self.pos.y < 0:
            self.pos.y = WORLD_HEIGHT
        elif self.pos.y > WORLD_HEIGHT:
            self.pos.y = 0

    @staticmethod
    def _random_position() -> pygame.Vector2:
        return pygame.Vector2(
            random.uniform(0, WORLD_WIDTH),
            random.uniform(0, WORLD_HEIGHT),
        )

    # ------------------------------------------------------------------
    # Private – Drawing
    # ------------------------------------------------------------------

    def _draw_status_bars(
        self,
        surface: pygame.Surface,
        px: int,
        py: int,
    ) -> None:
        """Draw three small bars (Hunger, Energy, Social) below the creature."""
        bars = [
            (self.hunger,          100, COLOR_BAR_HUNGER),
            (self.energy,          100, COLOR_BAR_ENERGY),
            (self.social,          100, COLOR_BAR_SOCIAL),
        ]
        start_x = px - BAR_WIDTH // 2
        start_y = py + CREATURE_RADIUS + BAR_SPACING

        for i, (value, maximum, color) in enumerate(bars):
            y = start_y + i * (BAR_HEIGHT + 2)
            # Background
            pygame.draw.rect(
                surface,
                COLOR_BAR_BG,
                (start_x, y, BAR_WIDTH, BAR_HEIGHT),
            )
            # Filled portion
            filled = max(0, min(BAR_WIDTH, int(BAR_WIDTH * value / maximum)))
            if filled:
                pygame.draw.rect(surface, color, (start_x, y, filled, BAR_HEIGHT))

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Creature(state={self.state.name}, "
            f"hunger={self.hunger:.1f}, "
            f"energy={self.energy:.1f}, "
            f"social={self.social:.1f})"
        )
