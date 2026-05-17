# =============================================================================
# PROJECT ECHO – creature.py
# Autonomous agent with stable state-machine AI, hysteresis, dying state,
# and a full life/death/corpse cycle.
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
    HUNGER_DECAY_RATE, ENERGY_DECAY_WANDER, ENERGY_DECAY_SEEK, ENERGY_REST_RATE,
    SOCIAL_DECAY_RATE, SOCIAL_GAIN_RATE,
    STATE_MIN_DURATION, STATE_EMERGENCY_HUNGER,
    HUNGER_SEEK_ENTER, HUNGER_SEEK_EXIT,
    ENERGY_REST_ENTER, ENERGY_REST_EXIT,
    SOCIAL_ENTER, SOCIAL_EXIT,
    WANDER_CHANGE_INTERVAL, WANDER_CIRCLE_DIST, WANDER_CIRCLE_RADIUS,
    WANDER_ANGLE_SPEED, SOCIAL_RADIUS,
    IDLE_CHANCE, IDLE_DURATION_MIN, IDLE_DURATION_MAX,
    FOOD_DETECTION_RADIUS, FOOD_DETECTION_RADIUS_HUNGRY, FOOD_HUNGER_SCAN_BOOST,
    FOOD_MEMORY_DURATION, FOOD_SAFE_SEEK_RADIUS,
    FOOD_CLAIM_OVERRIDE_FACTOR,
    CROWD_RADIUS, CROWD_THRESHOLD, CROWD_WANDER_BIAS, CROWD_LOG_COOLDOWN,
    TARGET_COMMIT_BASE, TARGET_COMMIT_VAR,
    TARGET_RETARGET_COOL, TARGET_BETTER_FACTOR,
    CLAIM_REFRESH_INTERVAL, CONTEST_LOG_COOLDOWN,
    SURVIVAL_LOG_COOLDOWN,
    DYING_ENERGY_THRESHOLD, DYING_HUNGER_THRESHOLD,
    DEATH_CRITICAL_TIME, CORPSE_DURATION,
    REL_SOCIAL_GAIN, REL_PASSIVE_GAIN, REL_COMPETITION_LOSS,
    REL_DECAY_RATE, REL_MAX, REL_MIN,
    REL_FRIEND_THRESHOLD, REL_FRIEND_PULL,
    PERS_RISK_TOLERANCE_MIN, PERS_RISK_TOLERANCE_MAX,
    PERS_LAZINESS_MIN, PERS_LAZINESS_MAX,
    PERS_SOCIAL_DEPENDENCY_MIN, PERS_SOCIAL_DEPENDENCY_MAX,
    PERS_FOOD_GREED_MIN, PERS_FOOD_GREED_MAX,
    ENERGY_SOCIAL_SUPPRESS, ENERGY_SURVIVAL_ONLY, ENERGY_MINIMAL_MOVE,
    REST_ENERGY_TARGET,
    WORLD_WIDTH, WORLD_HEIGHT,
    COLOR_CREATURE, COLOR_CREATURE_REST, COLOR_CREATURE_SOCIAL,
    COLOR_CREATURE_SEEK, COLOR_CREATURE_DYING, COLOR_CORPSE,
    COLOR_BAR_BG, COLOR_BAR_HUNGER, COLOR_BAR_ENERGY, COLOR_BAR_SOCIAL,
    SHOW_STATUS_BARS, BAR_WIDTH, BAR_HEIGHT, BAR_SPACING,
    SHOW_CREATURE_LABELS, LABEL_FONT_SIZE, LABEL_COLOR,
    DEBUG_SHOW_PERCEPTION,
)
from logger import get_logger

if TYPE_CHECKING:
    from world import World


# =============================================================================
class State(Enum):
    WANDER     = auto()
    SEEK_FOOD  = auto()
    REST       = auto()
    SOCIALIZE  = auto()
    DYING      = auto()


_STATE_COLOR = {
    State.WANDER:    COLOR_CREATURE,
    State.SEEK_FOOD: COLOR_CREATURE_SEEK,
    State.REST:      COLOR_CREATURE_REST,
    State.SOCIALIZE: COLOR_CREATURE_SOCIAL,
    State.DYING:     COLOR_CREATURE_DYING,
}


# Module-level label font – lazy-initialized after pygame.init()
_label_font: pygame.font.Font | None = None


def _get_label_font() -> pygame.font.Font:
    global _label_font
    if _label_font is None:
        _label_font = pygame.font.SysFont("Courier New", LABEL_FONT_SIZE)
    return _label_font


# =============================================================================
class Creature:
    """
    Autonomous creature driven by a stable priority state machine.

    State machine properties:
        - Hysteresis:   separate enter/exit thresholds prevent rapid oscillation
        - Commitment:   minimum time in each state (STATE_MIN_DURATION)
        - Emergency:    critical hunger always breaks commitment immediately
        - DYING:        pre-death degraded state with restricted behavior

    Extension hooks:
        self.memory        – episodic memory list
        self.dna           – heritable trait dict
        self.relationships – {creature_id: affinity_float}
    """

    _counter: int = 0

    def __init__(self, x: float, y: float) -> None:
        Creature._counter += 1
        self.label  = f"ECHO-{Creature._counter:02d}"
        self.id     = uuid.uuid4()
        self.pos    = pygame.Vector2(x, y)
        self.vel    = pygame.Vector2(
            random.uniform(-1, 1), random.uniform(-1, 1)
        ).normalize() * random.uniform(CREATURE_SPEED_MIN * 0.3, CREATURE_SPEED_MIN * 0.7)

        # --- Personality (sampled once, shapes all survival decisions) ---
        self._speed            = random.uniform(CREATURE_SPEED_MIN, CREATURE_SPEED_MAX)
        self.risk_tolerance    = random.uniform(PERS_RISK_TOLERANCE_MIN,    PERS_RISK_TOLERANCE_MAX)
        self.laziness          = random.uniform(PERS_LAZINESS_MIN,           PERS_LAZINESS_MAX)
        self.social_dependency = random.uniform(PERS_SOCIAL_DEPENDENCY_MIN,  PERS_SOCIAL_DEPENDENCY_MAX)
        self.food_greed        = random.uniform(PERS_FOOD_GREED_MIN,         PERS_FOOD_GREED_MAX)

        # --- Vital stats (0–100) ---
        self.hunger = random.uniform(20, 60)
        self.energy = random.uniform(50, 100)
        self.social = random.uniform(30, 90)

        # --- State machine ---
        self.state         = State.WANDER
        self._state_timer  = 0.0    # seconds spent in current state
        self._lifespan     = 0.0    # total seconds alive
        self.target        = None   # Food object or Creature reference

        # --- Life / Death ---
        self.alive           = True
        self.is_corpse       = False
        self._death_timer    = 0.0  # seconds at critical stats; reused for corpse fade
        self._cause_of_death : str | None = None

        # --- Wander / Reynolds wander circle ---
        self._wander_timer = 0.0
        self._wander_angle = random.uniform(0, math.tau)

        # --- Idle sub-state ---
        self._is_idle       = False
        self._idle_timer    = 0.0
        self._idle_duration = 0.0

        # --- Social interaction cooldown ---
        self._in_social_interaction = False

        # --- Food perception memory ---
        self._last_seen_food_pos : pygame.Vector2 | None = None
        self._food_memory_timer  : float = 0.0

        # --- Lifetime tracking (analytics / death summary) ---
        self.food_eaten          : int   = 0
        self.social_interactions : int   = 0
        self.distance_travelled  : float = 0.0
        self.time_resting        : float = 0.0
        self.time_socializing    : float = 0.0
        self.time_seeking_food   : float = 0.0
        self.time_wandering      : float = 0.0

        # Friendship milestones already logged (avoid duplicate events)
        self._logged_friends     : set   = set()

        # Anti-spam: SURVIVAL_DECISION log cooldown
        self._survival_log_timer : float = 0.0

        # Target commitment / retarget cooldowns
        self._target_commit_timer : float = 0.0   # time left before re-evaluation allowed
        self._retarget_cool       : float = 0.0   # cooldown after voluntary target switch
        self._claim_refresh_timer : float = 0.0   # time until next claim TTL refresh
        self._contest_log_timer   : float = 0.0   # rate limit for FOOD_CONTEST log
        self._crowd_log_timer     : float = 0.0   # rate limit for CROWD_AVOIDANCE log

        # --- Extension placeholders ---
        self.memory        : list = []
        self.dna           : dict = {}
        self.relationships : dict = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, world: "World", dt: float) -> None:
        """Main update tick – only called while self.alive is True."""
        self._lifespan    += dt
        self._state_timer += dt
        if self._survival_log_timer  > 0: self._survival_log_timer  = max(0.0, self._survival_log_timer  - dt)
        if self._target_commit_timer > 0: self._target_commit_timer = max(0.0, self._target_commit_timer - dt)
        if self._retarget_cool       > 0: self._retarget_cool       = max(0.0, self._retarget_cool       - dt)
        if self._claim_refresh_timer > 0: self._claim_refresh_timer = max(0.0, self._claim_refresh_timer - dt)
        if self._contest_log_timer   > 0: self._contest_log_timer   = max(0.0, self._contest_log_timer   - dt)
        if self._crowd_log_timer     > 0: self._crowd_log_timer     = max(0.0, self._crowd_log_timer     - dt)
        self._decay_stats(dt)

        # Decay food memory over time
        if self._last_seen_food_pos is not None:
            self._food_memory_timer += dt
            if self._food_memory_timer >= FOOD_MEMORY_DURATION:
                self._last_seen_food_pos = None
                self._food_memory_timer  = 0.0

        self._update_relationships(world, dt)
        self._decide_state(world, dt)
        if self.alive:  # _decide_state may have triggered death
            self._act(world, dt)
            self._move(dt)
            self._wrap_borders()

    def update_corpse(self, dt: float) -> None:
        """Advance corpse fade timer. Called by World when alive=False."""
        self._death_timer += dt
        if self._death_timer >= CORPSE_DURATION:
            self.is_corpse = False   # signals World to remove

    def draw(self, surface: pygame.Surface) -> None:
        """Render based on alive/dying/corpse status."""
        if self.is_corpse:
            self._draw_corpse(surface)
        elif self.state == State.DYING:
            self._draw_body(surface, COLOR_CREATURE_DYING, glow=False)
            if SHOW_STATUS_BARS:
                self._draw_status_bars(surface, int(self.pos.x), int(self.pos.y))
        else:
            px, py = int(self.pos.x), int(self.pos.y)
            if DEBUG_SHOW_PERCEPTION and self.state == State.SEEK_FOOD:
                self._draw_perception_debug(surface, px, py)
            self._draw_body(surface, _STATE_COLOR[self.state], glow=True)
            if SHOW_CREATURE_LABELS:
                self._draw_label(surface, px, py)
            if SHOW_STATUS_BARS:
                self._draw_status_bars(surface, px, py)

    # ------------------------------------------------------------------
    # Private – AI Decision
    # ------------------------------------------------------------------

    def _decide_state(self, world: "World", dt: float) -> None:
        """
        Stable priority state machine with:
          1. Death check (always runs, can interrupt everything)
          2. Emergency hunger override (breaks commitment)
          3. State commitment (min duration)
          4. Hysteresis evaluation (personality-modulated)
        """
        # 1. Death / dying check – always evaluated
        if self._check_death_conditions(world, dt):
            return

        # 2. DYING state restricts choices to SEEK_FOOD or REST only
        if self.state == State.DYING:
            if self.hunger >= HUNGER_SEEK_ENTER:
                nearest = self._get_food_target(world)
                if nearest is not None:
                    self._force_transition(State.SEEK_FOOD, world, "dying_hunger")
            elif self.energy <= ENERGY_REST_ENTER:
                self._force_transition(State.REST, world, "dying_rest")
            return

        # 3. Survival-only mode: critical energy → only REST or emergency food
        if self.energy < ENERGY_SURVIVAL_ONLY and self.state not in (
            State.REST, State.SEEK_FOOD
        ):
            self._log_survival(f"emergency_rest | energy={self.energy:.1f}")
            self._force_transition(State.REST, world, "emergency_rest")
            return

        # 4. Emergency: critical hunger always breaks commitment
        if self.hunger >= STATE_EMERGENCY_HUNGER and self.state != State.SEEK_FOOD:
            self._force_transition(State.SEEK_FOOD, world, "emergency_hunger")
            return

        # 5. Respect commitment – don't evaluate until min duration elapsed
        if self._state_timer < STATE_MIN_DURATION:
            return

        # 6. Hysteresis evaluation (personality-shifted)
        new_state = self._evaluate_next_state()
        if new_state != self.state:
            # Log when a social need was overridden by survival pressure
            if self.state == State.SOCIALIZE and new_state != State.SOCIALIZE:
                pass  # already handled – transitioning away naturally
            if new_state == State.WANDER and self.social <= SOCIAL_ENTER and (
                self.energy < ENERGY_SOCIAL_SUPPRESS
                or self.hunger > STATE_EMERGENCY_HUNGER * 0.8
            ):
                self._log_survival(
                    f"ignored_social | energy={self.energy:.1f} hunger={self.hunger:.1f}"
                )
            self._force_transition(new_state, world, "normal")

    def _evaluate_next_state(self) -> State:
        """
        Hysteresis-based state selection with personality-shifted thresholds
        and energy-aware social suppression.
        """
        # ----- Personality-adjusted thresholds -----
        # Lazier creatures enter REST sooner (higher effective threshold)
        rest_enter  = ENERGY_REST_ENTER  + self.laziness * 15
        # More socially dependent creatures enter SOCIALIZE at a lower social value
        social_enter = SOCIAL_ENTER - self.social_dependency * 10

        # ----- Sticky exits -----
        if self.state == State.SEEK_FOOD and self.hunger >= HUNGER_SEEK_EXIT:
            return State.SEEK_FOOD

        # REST: hold until reaching the recovery target (adjusted by laziness)
        if self.state == State.REST:
            recovery_target = REST_ENERGY_TARGET - (1.0 - self.laziness) * 15
            if self.energy < recovery_target:
                return State.REST

        if self.state == State.SOCIALIZE and self.social <= SOCIAL_EXIT:
            return State.SOCIALIZE

        # ----- Priority enter thresholds -----
        if self.hunger >= HUNGER_SEEK_ENTER:
            return State.SEEK_FOOD

        if self.energy <= rest_enter:
            return State.REST

        # Social suppression: ignore socialising when energy or food situation is bad
        social_suppressed = (
            self.energy < ENERGY_SOCIAL_SUPPRESS
            or self.hunger > STATE_EMERGENCY_HUNGER * 0.8
        )
        if not social_suppressed and self.social <= social_enter:
            return State.SOCIALIZE

        return State.WANDER

    def _force_transition(
        self,
        new_state : State,
        world     : "World",
        reason    : str,
    ) -> None:
        """Execute a state transition, log it with elapsed duration, update target."""
        old_state = self.state
        duration  = self._state_timer

        # Release food claim when leaving SEEK_FOOD without eating
        if old_state == State.SEEK_FOOD and self.target is not None:
            self._release_claim(self.target)

        target_dist = (
            f"  tgt={int(self.pos.distance_to(self.target.pos))}px"
            if self.target is not None and hasattr(self.target, "pos")
            else ""
        )
        get_logger().log_event(
            "STATE_CHANGE",
            (
                f"{old_state.name} ({duration:.1f}s) -> {new_state.name}"
                f"  [{reason}]"
                f"  h={self.hunger:.0f} e={self.energy:.0f} s={self.social:.0f}"
                f"{target_dist}"
            ),
            self.label,
        )

        # Extra survival log events on notable transitions
        if new_state == State.REST:
            if reason == "emergency_rest":
                rest_detail = f"emergency_rest | energy={self.energy:.1f}"
            elif self.energy <= ENERGY_REST_ENTER + self.laziness * 15:
                rest_detail = f"low_energy | energy={self.energy:.1f} laziness={self.laziness:.2f}"
            else:
                rest_detail = f"lazy_rest | energy={self.energy:.1f} laziness={self.laziness:.2f}"
            get_logger().log_event("REST_REASON", rest_detail, self.label)

        if new_state == State.SOCIALIZE and self.energy < ENERGY_SOCIAL_SUPPRESS:
            self._log_survival(
                f"socialising_low_energy | energy={self.energy:.1f}"
                f" social_dep={self.social_dependency:.2f}"
            )

        self.state        = new_state
        self._state_timer = 0.0

        # Refresh target for the new state
        if new_state == State.SEEK_FOOD:
            self.target = self._get_food_target(world)
            self._reset_commit_timer()
        elif new_state == State.SOCIALIZE:
            nearby      = world.get_nearby_creatures(self.pos, SOCIAL_RADIUS, exclude=self)
            self.target = self._best_social_target(nearby)
        else:
            self.target = None

    # ------------------------------------------------------------------
    # Private – Death System
    # ------------------------------------------------------------------

    def _check_death_conditions(self, world: "World", dt: float) -> bool:
        """
        Accumulate time spent at critical stats; trigger death when threshold met.
        Also transitions to DYING when stats are very low but not yet fatal.
        Returns True if the creature died this frame.
        """
        at_critical = (self.energy <= 0) or (self.hunger >= 100)

        if at_critical:
            self._death_timer += dt
            if self._death_timer >= DEATH_CRITICAL_TIME:
                self._die()
                return True
        else:
            # Slowly bleed off death timer when recovering
            self._death_timer = max(0.0, self._death_timer - dt * 0.5)

        # Pre-death DYING state: severely reduced capacity
        if (self.energy < DYING_ENERGY_THRESHOLD or
                self.hunger > DYING_HUNGER_THRESHOLD):
            if self.state not in (State.DYING, State.REST, State.SEEK_FOOD):
                self._force_transition(State.DYING, world, "critical_stats")

        return False

    def _die(self) -> None:
        """Mark creature as dead, log death event + full life summary, start corpse fade."""
        self._cause_of_death = "starvation" if self.hunger >= 100 else "exhaustion"
        get_logger().log_event(
            "DEATH",
            (
                f"cause={self._cause_of_death} | "
                f"lifespan={self._lifespan:.1f}s | "
                f"state={self.state.name} | "
                f"hunger={self.hunger:.1f} | "
                f"energy={self.energy:.1f}"
            ),
            self.label,
        )
        get_logger().log_lifetime_summary(self)
        # Release any held food claim so others can take it
        if self.target is not None:
            self._release_claim(self.target)
        self.alive        = False
        self.is_corpse    = True
        self._death_timer = 0.0   # reset – now used for corpse fade

    # ------------------------------------------------------------------
    # Private – Behavior (Act)
    # ------------------------------------------------------------------

    def _act(self, world: "World", dt: float) -> None:
        """Translate current state into movement and interaction."""
        if self.state == State.SEEK_FOOD:
            if self.target is not None and self.target.alive:
                # Refresh claim TTL periodically (not every frame)
                if self._claim_refresh_timer <= 0:
                    self._claim(self.target)
                    self._claim_refresh_timer = CLAIM_REFRESH_INTERVAL

                self._steer_arrive(self.target.pos)
                if self.pos.distance_to(self.target.pos) < CREATURE_RADIUS + self.target.radius:
                    self._eat(self.target, world)
                elif self._target_commit_timer <= 0 and self._retarget_cool <= 0:
                    # Commitment expired – consider whether a better target exists
                    self._consider_retarget(world)
            else:
                # Target gone or None – acquire a fresh one immediately
                self._acquire_new_target(world)
                if self.target is not None:
                    self._steer_arrive(self.target.pos)
                elif self._last_seen_food_pos is not None:
                    self._steer_arrive(self._last_seen_food_pos)
                    if self.pos.distance_to(self._last_seen_food_pos) < 20:
                        self._last_seen_food_pos = None
                else:
                    self._steer_search_wander(dt)

        elif self.state == State.REST:
            self.vel *= max(0.0, 1.0 - dt * 4)

        elif self.state == State.SOCIALIZE:
            if self.target is not None and self.target.alive:
                self._steer_arrive(self.target.pos)
                if self.pos.distance_to(self.target.pos) < SOCIAL_RADIUS * 0.5:
                    self.social = min(100, self.social + SOCIAL_GAIN_RATE * dt)
                    if not self._in_social_interaction:
                        self._in_social_interaction  = True
                        self.social_interactions    += 1
                        get_logger().log_event(
                            "SOCIAL",
                            f"interacting with {self.target.label}  total={self.social_interactions}",
                            self.label,
                        )
                        get_logger().increment_social()
                else:
                    self._in_social_interaction = False
            else:
                self._in_social_interaction = False
                # Pick best friend among newly visible creatures
                nearby = world.get_nearby_creatures(self.pos, SOCIAL_RADIUS, exclude=self)
                self.target = self._best_social_target(nearby)
                if self.target is None:
                    self._steer_wander(world, dt)

        elif self.state == State.DYING:
            self.vel *= max(0.0, 1.0 - dt * 2)

        else:  # WANDER
            self._steer_wander(world, dt)

    # ------------------------------------------------------------------
    # Private – Steering
    # ------------------------------------------------------------------

    def _steer_arrive(self, target_pos: pygame.Vector2) -> None:
        """
        Arrive steering: slows down near target.
        At critical energy levels acceleration and speed are heavily reduced.
        """
        to_target = target_pos - self.pos
        dist      = to_target.length()
        if dist < 0.1:
            return

        energy_factor   = 0.5 + 0.5 * (self.energy / 100)
        effective_speed = self._speed * energy_factor

        if self.energy < ENERGY_MINIMAL_MOVE:
            # Near-death crawl: tiny acceleration, minimal speed
            effective_speed *= 0.15
            lerp = CREATURE_ACCEL_FACTOR * 0.2
        elif self.state == State.SEEK_FOOD:
            # Risk-tolerant creatures push harder when hungry
            speed_boost = 1.2 + self.risk_tolerance * 0.4
            effective_speed *= speed_boost
            lerp = CREATURE_ACCEL_FACTOR * (1.4 + self.risk_tolerance * 0.6)
        elif self.state == State.DYING:
            effective_speed *= 0.4
            lerp = CREATURE_ACCEL_FACTOR * 0.5
        elif self.energy < ENERGY_SURVIVAL_ONLY:
            # Low-energy: softer corrections, conserve momentum
            effective_speed *= 0.6
            lerp = CREATURE_ACCEL_FACTOR * 0.5
        elif self.energy < ENERGY_SOCIAL_SUPPRESS:
            # Reduced efficiency at moderate-low energy
            effective_speed *= 0.8
            lerp = CREATURE_ACCEL_FACTOR * 0.75
        else:
            lerp = CREATURE_ACCEL_FACTOR

        if dist < CREATURE_ARRIVE_RADIUS:
            effective_speed *= dist / CREATURE_ARRIVE_RADIUS

        desired_vel = to_target.normalize() * effective_speed
        self.vel    = self.vel.lerp(desired_vel, lerp)

    def _steer_wander(self, world: "World", dt: float) -> None:
        """Reynolds Wander Circle with periodic idle pauses and friend-pull bias."""
        # --- Idle sub-state ---
        if self._is_idle:
            self._idle_timer += dt
            self.vel *= max(0.0, 1.0 - dt * 5)
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
                get_logger().log_event(
                    "IDLE_ENTER",
                    f"pausing for {self._idle_duration:.1f}s",
                    self.label,
                )
                return

        # --- Friend pull (gentle bias toward nearest friend) ---
        self._apply_friend_pull(world, dt)

        # --- Crowd avoidance (gentle bias away from seeker clusters) ---
        self._apply_crowd_avoidance(world, dt)

        # --- Perturb wander angle ---
        self._wander_angle += random.uniform(-WANDER_ANGLE_SPEED, WANDER_ANGLE_SPEED) * dt

        # --- Project wander circle ---
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

    def _update_relationships(self, world: "World", dt: float) -> None:
        """
        Update affinity values with nearby creatures.
        - Passive gain from proximity
        - Stronger gain while actively socializing
        - Slow decay over time (forgetting)
        """
        nearby = world.get_nearby_creatures(self.pos, SOCIAL_RADIUS, exclude=self)

        # Decay all existing relationships
        for data in self.relationships.values():
            data["affinity"] = max(REL_MIN, data["affinity"] - REL_DECAY_RATE * dt)

        # Update proximity-based affinity
        for c in nearby:
            if c.id not in self.relationships:
                self.relationships[c.id] = {
                    "affinity"      : 0.0,
                    "label"         : c.label,
                    "last_seen_time": 0.0,
                }
            entry = self.relationships[c.id]
            entry["last_seen_time"] = self._lifespan
            prev_affinity = entry["affinity"]
            entry["affinity"] = min(REL_MAX, entry["affinity"] + REL_PASSIVE_GAIN * dt)

            # Extra gain when this creature is our active social target
            if self.state == State.SOCIALIZE and self.target is c:
                entry["affinity"] = min(REL_MAX,
                    entry["affinity"] + REL_SOCIAL_GAIN * dt)

            # Log first-time friendship milestone
            if (prev_affinity < REL_FRIEND_THRESHOLD
                    <= entry["affinity"]
                    and c.id not in self._logged_friends):
                self._logged_friends.add(c.id)
                get_logger().log_relationship(
                    "BEST_FRIEND", self.label, c.label, entry["affinity"]
                )

    def _best_social_target(self, nearby: list) -> "Creature | None":
        """Pick the nearby creature with the highest known affinity."""
        if not nearby:
            return None

        def affinity(c):
            d = self.relationships.get(c.id)
            return d["affinity"] if d else 0.0

        return max(nearby, key=affinity)

    def _apply_friend_pull(self, world: "World", dt: float) -> None:
        """Gently bias the wander angle toward the nearest friend."""
        best, best_aff = None, REL_FRIEND_THRESHOLD
        for c in world.get_nearby_creatures(self.pos, SOCIAL_RADIUS, exclude=self):
            d = self.relationships.get(c.id)
            if d and d["affinity"] > best_aff:
                best_aff, best = d["affinity"], c
        if best is None:
            return
        to_friend = best.pos - self.pos
        if to_friend.length() < 1.0:
            return
        friend_angle = math.atan2(to_friend.y, to_friend.x)
        diff = friend_angle - self._wander_angle
        while diff >  math.pi: diff -= math.tau
        while diff < -math.pi: diff += math.tau
        self._wander_angle += diff * REL_FRIEND_PULL * dt

    def _apply_crowd_avoidance(self, world: "World", dt: float) -> None:
        """Gently bias wander angle away from overcrowded SEEK_FOOD clusters."""
        radius  = CROWD_RADIUS * 1.5
        seekers = [
            c for c in world.get_nearby_creatures(self.pos, radius, exclude=self)
            if c.state == State.SEEK_FOOD
        ]
        if len(seekers) < CROWD_THRESHOLD:
            return

        cx = sum(c.pos.x for c in seekers) / len(seekers)
        cy = sum(c.pos.y for c in seekers) / len(seekers)
        away_angle = math.atan2(self.pos.y - cy, self.pos.x - cx)

        pressure = min(1.0, (len(seekers) - CROWD_THRESHOLD) / 5.0)
        diff = away_angle - self._wander_angle
        while diff >  math.pi: diff -= math.tau
        while diff < -math.pi: diff += math.tau
        self._wander_angle += diff * CROWD_WANDER_BIAS * pressure * dt

        if self._crowd_log_timer <= 0:
            get_logger().log_event(
                "CROWD_AVOIDANCE",
                f"seekers_nearby={len(seekers)} pressure={pressure:.2f}",
                self.label,
            )
            self._crowd_log_timer = CROWD_LOG_COOLDOWN

    def _get_food_target(self, world: "World"):
        """
        Claim-aware food lookup. Uses get_best_food_target for claim coordination.

        Priority order:
          1. Critically low energy → safe radius, claim result; cautious creatures
             refuse long trips if nothing found nearby
          2. Hungry → expanded radius boosted by food_greed personality
          3. Normal → standard detection radius
        """
        # --- Critically low energy: try the safe short radius first ---
        if self.energy < ENERGY_SURVIVAL_ONLY:
            food = world.get_best_food_target(self.pos, FOOD_SAFE_SEEK_RADIUS, self)
            if food is not None:
                self._claim(food)
                return food
            # No nearby food – cautious creatures refuse the risky long trip
            if self.risk_tolerance < 0.5:
                return None
            self._log_survival(
                f"risky_food_search | energy={self.energy:.1f} risk={self.risk_tolerance:.2f}"
            )

        # --- Normal / hungry scan – food_greed widens hungry perception ---
        if self.hunger >= FOOD_HUNGER_SCAN_BOOST:
            greed_boost = 1.0 + self.food_greed * 0.5  # up to 1.5×
            radius = FOOD_DETECTION_RADIUS_HUNGRY * greed_boost
        else:
            radius = FOOD_DETECTION_RADIUS

        food = world.get_best_food_target(self.pos, radius, self)

        if food is not None:
            # If chosen food has no competition but nearest raw food was contested,
            # log a migration decision so analysts can see the crowd-driven rerouting.
            chosen_seekers = getattr(world, "_last_food_seekers", 0)
            if chosen_seekers == 0:
                nearest_contested = any(
                    f.claimed_by is not None
                    and self.pos.distance_squared_to(f.pos) < radius * radius
                    for f in world.foods
                    if f is not food
                )
                if nearest_contested:
                    get_logger().log_event(
                        "MIGRATION_DECISION",
                        f"avoided contested zone  chose ({int(food.pos.x)},{int(food.pos.y)})",
                        self.label,
                    )
            self._claim(food)
        return food

    # ------------------------------------------------------------------
    # Target commitment helpers
    # ------------------------------------------------------------------

    def _reset_commit_timer(self) -> None:
        """
        Set the commitment timer based on personality.
        Risk-tolerant creatures commit for shorter periods (quicker to reassess).
        Cautious creatures hold their target longer (more decisive, less twitchy).
        """
        duration = TARGET_COMMIT_BASE + (1.0 - self.risk_tolerance) * TARGET_COMMIT_VAR
        self._target_commit_timer = duration

    def _acquire_new_target(self, world: "World") -> None:
        """Find and claim a fresh food target with no prior commitment check."""
        self.target = self._get_food_target(world)
        if self.target is not None:
            self._reset_commit_timer()

    def _consider_retarget(self, world: "World") -> None:
        """
        Called when the commitment timer expires.  Checks break conditions and
        whether a significantly better (closer) target exists before switching.
        Always resets the commit timer so evaluations stay periodic.
        """
        # Break condition: emergency hunger – always seek the best option
        if self.hunger >= STATE_EMERGENCY_HUNGER:
            self._acquire_new_target(world)
            return

        # Break condition: current target too far (creature may be stuck / path blocked)
        if self.target is not None and self.target.alive:
            current_dist = self.pos.distance_to(self.target.pos)
            if current_dist > FOOD_DETECTION_RADIUS * 1.5:
                self._acquire_new_target(world)
                return

            # Opportunistic switch: only if a clearly closer unclaimed food exists
            candidate = world.get_best_food_target(self.pos, FOOD_DETECTION_RADIUS, self)
            if (candidate is not None
                    and candidate is not self.target
                    and self.pos.distance_to(candidate.pos) < current_dist * TARGET_BETTER_FACTOR):
                self._release_claim(self.target)
                self._claim(candidate)
                self.target         = candidate
                self._retarget_cool = TARGET_RETARGET_COOL

        # Reset commit timer regardless of outcome (keep evaluations periodic)
        self._reset_commit_timer()

    # ------------------------------------------------------------------

    def _log_survival(self, message: str) -> None:
        """Rate-limited SURVIVAL_DECISION log (max once per SURVIVAL_LOG_COOLDOWN seconds)."""
        if self._survival_log_timer <= 0:
            get_logger().log_event("SURVIVAL_DECISION", message, self.label)
            self._survival_log_timer = SURVIVAL_LOG_COOLDOWN

    def _claim(self, food: "Food") -> None:
        """
        Soft-claim a food item for this creature.
        Resets the TTL timer; logs FOOD_CLAIM or FOOD_CONTEST.
        Also fires TARGET_SWITCH if this creature was already heading elsewhere.
        """
        if food.claimed_by == self.id:
            food._claim_timer = 0.0   # refresh TTL while still targeting
            return

        was_contested = food.claimed_by is not None

        # Log TARGET_SWITCH when already mid-seek toward a different food
        if (self.state == State.SEEK_FOOD
                and self.target is not None
                and self.target is not food
                and hasattr(self.target, "pos")):
            get_logger().log_event(
                "TARGET_SWITCH",
                f"({int(self.target.pos.x)},{int(self.target.pos.y)})"
                f" -> ({int(food.pos.x)},{int(food.pos.y)})",
                self.label,
            )

        food.claimed_by   = self.id
        food._claim_timer = 0.0
        self._last_seen_food_pos = food.pos.copy()
        self._food_memory_timer  = 0.0

        if was_contested:
            # Rate-limited: don't spam FOOD_CONTEST every frame
            if self._contest_log_timer <= 0:
                get_logger().log_event(
                    "FOOD_CONTEST",
                    f"food at ({int(food.pos.x)},{int(food.pos.y)})",
                    self.label,
                )
                self._contest_log_timer = CONTEST_LOG_COOLDOWN
        else:
            get_logger().log_event(
                "FOOD_CLAIM",
                f"food at ({int(food.pos.x)},{int(food.pos.y)})",
                self.label,
            )

    def _release_claim(self, food: "Food") -> None:
        """Release this creature's claim on a food item."""
        if hasattr(food, "claimed_by") and food.claimed_by == self.id:
            food.claimed_by   = None
            food._claim_timer = 0.0
            get_logger().log_event(
                "FOOD_CLAIM_RELEASE",
                f"food at ({int(food.pos.x)},{int(food.pos.y)})",
                self.label,
            )

    def _steer_search_wander(self, dt: float) -> None:
        """
        Faster, wider sweep used during SEEK_FOOD when no food or memory is available.
        No idle pauses – hunger forbids stopping.
        """
        self._wander_angle += random.uniform(
            -WANDER_ANGLE_SPEED * 2, WANDER_ANGLE_SPEED * 2
        ) * dt

        if self.vel.length() > 1.0:
            ahead = self.vel.normalize() * (WANDER_CIRCLE_DIST * 1.5)
        else:
            ahead = pygame.Vector2(
                math.cos(self._wander_angle),
                math.sin(self._wander_angle),
            ) * (WANDER_CIRCLE_DIST * 1.5)

        circle_center = self.pos + ahead
        search_target = circle_center + pygame.Vector2(
            math.cos(self._wander_angle) * WANDER_CIRCLE_RADIUS,
            math.sin(self._wander_angle) * WANDER_CIRCLE_RADIUS,
        )
        self._steer_arrive(search_target)

    # ------------------------------------------------------------------
    # Private – Stats
    # ------------------------------------------------------------------

    def _decay_stats(self, dt: float) -> None:
        """Drain stats over time; energy cost differs per state. Also tracks time per state."""
        self.hunger = min(100, self.hunger + HUNGER_DECAY_RATE * dt)

        if self.state == State.REST:
            self.energy = min(100, self.energy + ENERGY_REST_RATE * dt)
            self.time_resting       += dt
        elif self.state == State.SEEK_FOOD:
            self.energy = max(0, self.energy - ENERGY_DECAY_SEEK * dt)
            self.time_seeking_food  += dt
        elif self.state == State.SOCIALIZE:
            self.energy = max(0, self.energy - ENERGY_DECAY_WANDER * dt)
            self.time_socializing   += dt
        elif self.state == State.DYING:
            self.energy = max(0, self.energy - ENERGY_DECAY_WANDER * 0.5 * dt)
        else:  # WANDER
            self.energy = max(0, self.energy - ENERGY_DECAY_WANDER * dt)
            self.time_wandering     += dt

        if self.state != State.SOCIALIZE:
            self.social = max(0, self.social - SOCIAL_DECAY_RATE * dt)

    def _eat(self, food, world: "World") -> None:
        """Consume food. Apply competition penalty to any rival that was targeting it."""
        self.hunger      = max(0, self.hunger - food.nutrition)
        food.alive       = False
        self.target      = None
        self.food_eaten += 1
        get_logger().increment_food_consumed()
        get_logger().log_event(
            "FOOD_FOUND",
            f"ate at ({int(self.pos.x)}, {int(self.pos.y)})  total={self.food_eaten}",
            self.label,
        )
        # Penalize rivals who were also heading for this food
        for c in world.creatures:
            if c.alive and c is not self and c.target is food:
                if c.id not in self.relationships:
                    self.relationships[c.id] = {
                        "affinity"      : 0.0,
                        "label"         : c.label,
                        "last_seen_time": self._lifespan,
                    }
                old_aff = self.relationships[c.id]["affinity"]
                new_aff = max(REL_MIN, old_aff - REL_COMPETITION_LOSS)
                self.relationships[c.id]["affinity"] = new_aff
                get_logger().log_relationship(
                    "RIVALRY", self.label, c.label, new_aff,
                    delta=new_aff - old_aff,
                )

    # ------------------------------------------------------------------
    # Private – Physics
    # ------------------------------------------------------------------

    def _move(self, dt: float) -> None:
        """Apply friction, cap velocity, integrate position."""
        self.vel *= max(0.0, 1.0 - CREATURE_FRICTION * dt)

        energy_factor = 0.5 + 0.5 * (self.energy / 100)
        max_speed     = self._speed * energy_factor

        if self.energy < ENERGY_MINIMAL_MOVE:
            max_speed = self._speed * 0.12          # near-death crawl
        elif self.state == State.SEEK_FOOD:
            max_speed *= 1.2 + self.risk_tolerance * 0.4
        elif self.state == State.DYING:
            max_speed *= 0.3
        elif self.energy < ENERGY_SURVIVAL_ONLY:
            max_speed *= 0.55                       # conserve energy while moving
        elif self.energy < ENERGY_SOCIAL_SUPPRESS:
            max_speed *= 0.75

        if self.vel.length() > max_speed:
            self.vel = self.vel.normalize() * max_speed

        self.pos                += self.vel * dt
        self.distance_travelled += self.vel.length() * dt

    def _wrap_borders(self) -> None:
        if self.pos.x < 0:
            self.pos.x = WORLD_WIDTH
        elif self.pos.x > WORLD_WIDTH:
            self.pos.x = 0
        if self.pos.y < 0:
            self.pos.y = WORLD_HEIGHT
        elif self.pos.y > WORLD_HEIGHT:
            self.pos.y = 0

    # ------------------------------------------------------------------
    # Private – Rendering
    # ------------------------------------------------------------------

    def _draw_perception_debug(self, surface: pygame.Surface, px: int, py: int) -> None:
        """Optional: draw the food detection radius when DEBUG_SHOW_PERCEPTION is on."""
        r = (FOOD_DETECTION_RADIUS_HUNGRY
             if self.hunger >= FOOD_HUNGER_SCAN_BOOST
             else FOOD_DETECTION_RADIUS)
        pygame.draw.circle(surface, (60, 40, 0), (px, py), int(r), 1)

    def _draw_body(
        self,
        surface : pygame.Surface,
        color   : tuple,
        glow    : bool,
    ) -> None:
        px, py = int(self.pos.x), int(self.pos.y)

        if glow:
            glow_r    = CREATURE_RADIUS + 5
            glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*color, 40), (glow_r, glow_r), glow_r)
            surface.blit(glow_surf, (px - glow_r, py - glow_r))

        pygame.draw.circle(surface, color, (px, py), CREATURE_RADIUS)

    def _draw_corpse(self, surface: pygame.Surface) -> None:
        """Render a fading corpse dot."""
        px, py = int(self.pos.x), int(self.pos.y)
        t      = min(1.0, self._death_timer / CORPSE_DURATION)
        alpha  = int(200 * (1.0 - t))
        if alpha <= 0:
            return
        corpse_surf = pygame.Surface(
            (CREATURE_RADIUS * 2 + 2, CREATURE_RADIUS * 2 + 2), pygame.SRCALPHA
        )
        pygame.draw.circle(
            corpse_surf,
            (*COLOR_CORPSE, alpha),
            (CREATURE_RADIUS + 1, CREATURE_RADIUS + 1),
            CREATURE_RADIUS,
        )
        surface.blit(corpse_surf, (px - CREATURE_RADIUS - 1, py - CREATURE_RADIUS - 1))

    def _draw_label(self, surface: pygame.Surface, px: int, py: int) -> None:
        font   = _get_label_font()
        y_base = py - CREATURE_RADIUS - 14
        # Shadow (1 px offset) for contrast on dark background
        shadow = font.render(self.label, True, (0, 0, 0))
        surface.blit(shadow, (px - shadow.get_width() // 2 + 1, y_base + 1))
        # Main label
        text = font.render(self.label, True, LABEL_COLOR)
        surface.blit(text, (px - text.get_width() // 2, y_base))

    def _draw_status_bars(self, surface: pygame.Surface, px: int, py: int) -> None:
        bars    = [
            (self.hunger, 100, COLOR_BAR_HUNGER),
            (self.energy, 100, COLOR_BAR_ENERGY),
            (self.social, 100, COLOR_BAR_SOCIAL),
        ]
        start_x = px - BAR_WIDTH // 2
        start_y = py + CREATURE_RADIUS + BAR_SPACING

        for i, (value, maximum, color) in enumerate(bars):
            y = start_y + i * (BAR_HEIGHT + 2)
            pygame.draw.rect(surface, COLOR_BAR_BG, (start_x, y, BAR_WIDTH, BAR_HEIGHT))
            filled = max(0, min(BAR_WIDTH, int(BAR_WIDTH * value / maximum)))
            if filled:
                pygame.draw.rect(surface, color, (start_x, y, filled, BAR_HEIGHT))

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        status = "CORPSE" if self.is_corpse else self.state.name
        return (
            f"Creature({self.label} state={status}, "
            f"hunger={self.hunger:.1f}, "
            f"energy={self.energy:.1f}, "
            f"social={self.social:.1f})"
        )
