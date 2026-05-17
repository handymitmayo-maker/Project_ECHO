# =============================================================================
# PROJECT ECHO – observer.py
# Simulation observer: selection, freeze, overlays, profile dump.
#
# Camera pan/zoom/follow require decoupling WORLD_* from WINDOW_* (future).
# =============================================================================

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pygame

import settings
from settings import (
    CREATURE_RADIUS,
    COLOR_SELECTION_RING,
    INSPECTOR_PICK_SLOP,
)
from inspector_panel import InspectorPanel
from lineage_utils import lineage_tint
from logger import get_logger

if TYPE_CHECKING:
    from creature import Creature
    from world import World


class SimulationObserver:
    """Click-to-inspect observer with optional freeze and future camera hooks."""

    def __init__(self) -> None:
        self.selected: "Creature | None" = None
        self.frozen: bool = False
        self.follow_enabled: bool = False
        self.lineage_highlight_id: uuid.UUID | None = None
        self.generation_highlight: int | None = None
        self._panel = InspectorPanel()

    def handle_event(self, event: pygame.event.Event, world: "World") -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            picked = world.creature_at_pos(pygame.Vector2(event.pos))
            self.selected = picked
            return True

        if event.type != pygame.KEYDOWN:
            return False

        if event.key == pygame.K_f:
            self.frozen = not self.frozen
            return True

        if event.key == pygame.K_i:
            self.dump_profile_to_logger(world)
            return True

        return False

    def pick_at(self, screen_pos: tuple[int, int], world: "World") -> "Creature | None":
        return world.creature_at_pos(pygame.Vector2(screen_pos))

    def dump_profile_to_logger(self, world: "World") -> None:
        if self.selected is None:
            return
        get_logger().log_creature_profile(self.selected, world)

    def update(self, dt: float, world: "World") -> None:
        del dt, world
        # follow_enabled: stub until camera offset exists

    def draw_overlays(self, screen: pygame.Surface, world: "World") -> None:
        if settings.DEBUG_SHOW_LINEAGE_TINT:
            self._draw_lineage_tints(screen, world)
        if self.selected is not None and (self.selected.alive or self.selected.is_corpse):
            self._draw_selection_ring(screen, self.selected)

    def draw_inspector(self, screen: pygame.Surface, world: "World") -> None:
        if self.selected is not None:
            self._panel.draw(screen, self.selected, world)

    def clear_selection(self) -> None:
        self.selected = None

    def set_follow(self, creature: "Creature | None") -> None:
        self.follow_enabled = creature is not None
        if creature is not None:
            self.selected = creature

    def set_lineage_filter(self, lineage_id: uuid.UUID | None) -> None:
        self.lineage_highlight_id = lineage_id

    def set_generation_highlight(self, generation: int | None) -> None:
        self.generation_highlight = generation

    def highlight_oldest_survivor(self, world: "World") -> None:
        alive = [c for c in world.creatures if c.alive]
        if not alive:
            return
        oldest = max(alive, key=lambda c: c._lifespan)
        self.selected = oldest

    def _draw_selection_ring(self, screen: pygame.Surface, creature: "Creature") -> None:
        r = max(8, int(CREATURE_RADIUS * creature.scale) + 6)
        pygame.draw.circle(
            screen,
            COLOR_SELECTION_RING,
            (int(creature.pos.x), int(creature.pos.y)),
            r,
            2,
        )

    def _draw_lineage_tints(self, screen: pygame.Surface, world: "World") -> None:
        for c in world.creatures:
            if not c.alive or c.generation == 0:
                continue
            tint = lineage_tint(c.lineage_id)
            r = max(4, int(CREATURE_RADIUS * c.scale))
            pygame.draw.circle(
                screen,
                tint,
                (int(c.pos.x), int(c.pos.y)),
                r + 2,
                1,
            )
