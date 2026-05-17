# =============================================================================
# PROJECT ECHO – ui_panels.py
# Shared retro HUD panel renderer.
# =============================================================================

from __future__ import annotations

import pygame

from settings import (
    HUD_BG_COLOR, HUD_BG_ALPHA, HUD_TEXT_COLOR, HUD_TEXT_SHADOW,
    HUD_PADDING, HUD_LINE_HEIGHT,
)


def draw_panel(
    screen: pygame.Surface,
    font: pygame.font.Font,
    lines: list[str],
    x: int,
    y: int,
) -> tuple[int, int]:
    """Draw semi-transparent panel; return (width, height)."""
    if not lines:
        return 0, 0

    pad     = HUD_PADDING
    text_w  = max(font.size(line)[0] for line in lines)
    text_h  = HUD_LINE_HEIGHT * len(lines)
    panel_w = text_w + pad * 2
    panel_h = text_h + pad * 2

    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((*HUD_BG_COLOR, HUD_BG_ALPHA))
    screen.blit(panel, (x, y))

    tx = x + pad
    ty = y + pad
    for line in lines:
        screen.blit(font.render(line, True, HUD_TEXT_SHADOW), (tx + 1, ty + 1))
        screen.blit(font.render(line, True, HUD_TEXT_COLOR), (tx, ty))
        ty += HUD_LINE_HEIGHT

    return panel_w, panel_h
