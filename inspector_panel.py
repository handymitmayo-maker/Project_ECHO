# =============================================================================
# PROJECT ECHO – inspector_panel.py
# Retro research-terminal creature inspector panel.
# =============================================================================

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from settings import WINDOW_WIDTH, HUD_FONT_SIZE
from lineage_utils import format_creature_profile
from ui_panels import draw_panel

if TYPE_CHECKING:
    from creature import Creature
    from world import World


class InspectorPanel:
    """Right-side creature profile overlay."""

    def __init__(self) -> None:
        self._font = pygame.font.SysFont("Courier New", HUD_FONT_SIZE)

    def draw(
        self,
        screen: pygame.Surface,
        creature: "Creature",
        world: "World",
    ) -> None:
        lines = ["=== CREATURE INSPECTOR ===", *format_creature_profile(creature, world)]
        text_w = max(self._font.size(line)[0] for line in lines)
        pad = 10
        x = WINDOW_WIDTH - text_w - pad * 2 - 12
        y = 12
        draw_panel(screen, self._font, lines, x, y)
