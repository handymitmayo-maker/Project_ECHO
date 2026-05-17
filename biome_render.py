# =============================================================================
# PROJECT ECHO – biome_render.py
# Pre-renders smooth biome zone overlays (fill, ring border, type label).
# =============================================================================

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from settings import (
    WORLD_WIDTH, WORLD_HEIGHT,
    BIOME_ALPHA_CENTER, BIOME_FALLOFF,
    BIOME_RING_WIDTH, BIOME_RING_ALPHA,
    BIOME_SHOW_LABELS, BIOME_LABEL_FONT_SIZE,
    COLOR_BIOME_LABEL, COLOR_BIOME_LABEL_BG,
)

if TYPE_CHECKING:
    from world import Biome


# Display names and short codes per biome type
_BIOME_LABELS = {
    "fertile": ("FERTILE",  "▲"),
    "neutral": ("NEUTRAL",  "○"),
    "barren":  ("BARREN",   "▼"),
}

# Draw order: barren at bottom, fertile on top when zones overlap
_DRAW_ORDER = ("barren", "neutral", "fertile")


def _smoothstep(t: float) -> float:
    """Hermite ease 0→1 for soft edges without banding."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _patch_alpha(dist_norm: float, falloff: float) -> int:
    """
    Alpha from centre (1) to rim (0).
    dist_norm: 0 at centre, 1 at biome radius.
    """
    if dist_norm >= 1.0:
        return 0
    t = _smoothstep(1.0 - dist_norm)
    t = t ** (1.0 / max(0.5, falloff))
    return int(t * BIOME_ALPHA_CENTER)


def _render_radial_patch(biome: "Biome") -> pygame.Surface:
    """Build one biome as a smooth radial tint + ring on a local surface."""
    r = int(biome.radius) + BIOME_RING_WIDTH + 6
    size = r * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = r
    color = biome.color
    falloff = BIOME_FALLOFF
    steps = max(32, int(biome.radius // 4))  # more steps on large zones = smoother

    # Outer → inner filled rings with smoothstep alpha (fast, no banding)
    for i in range(steps, 0, -1):
        frac = i / steps
        ring_r = max(1, int(biome.radius * frac))
        alpha = _patch_alpha(frac, falloff)
        if alpha <= 0:
            continue
        pygame.draw.circle(surf, (*color, alpha), (cx, cy), ring_r)

    # Crisp outer boundary so each zone reads as its own region
    if BIOME_RING_WIDTH > 0 and BIOME_RING_ALPHA > 0:
        ring_color = (
            min(255, color[0] + 40),
            min(255, color[1] + 40),
            min(255, color[2] + 40),
            BIOME_RING_ALPHA,
        )
        pygame.draw.circle(
            surf, ring_color, (cx, cy), int(biome.radius),
            width=BIOME_RING_WIDTH,
        )

    if BIOME_SHOW_LABELS:
        _draw_biome_label(surf, biome, cx, cy)

    return surf


def _draw_biome_label(
    surf: pygame.Surface,
    biome: "Biome",
    cx: int,
    cy: int,
) -> None:
    """Type name + icon centred in the biome patch."""
    name, icon = _BIOME_LABELS.get(biome.type, (biome.type.upper(), "·"))
    font = pygame.font.SysFont("Courier New", BIOME_LABEL_FONT_SIZE, bold=True)

    icon_s = font.render(icon, True, COLOR_BIOME_LABEL)
    name_s = font.render(name, True, COLOR_BIOME_LABEL)
    tw = max(icon_s.get_width(), name_s.get_width())
    th = icon_s.get_height() + name_s.get_height() + 2
    pad = 6

    panel = pygame.Surface((tw + pad * 2, th + pad * 2), pygame.SRCALPHA)
    panel.fill(COLOR_BIOME_LABEL_BG)
    px = pad
    panel.blit(icon_s, (px + (tw - icon_s.get_width()) // 2, pad))
    panel.blit(name_s, (px + (tw - name_s.get_width()) // 2, pad + icon_s.get_height() + 2))

    surf.blit(panel, (cx - panel.get_width() // 2, cy - panel.get_height() // 2))


def build_biome_overlay(biomes: list["Biome"]) -> pygame.Surface:
    """
    Compose all biome patches onto one full-world SRCALPHA surface.
    Patches are ordered so fertile zones paint over barren where they overlap.
    """
    overlay = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT), pygame.SRCALPHA)

    by_type: dict[str, list] = {t: [] for t in _DRAW_ORDER}
    for b in biomes:
        if b.type in by_type:
            by_type[b.type].append(b)
        else:
            by_type.setdefault("neutral", []).append(b)

    for btype in _DRAW_ORDER:
        for biome in by_type.get(btype, []):
            patch = _render_radial_patch(biome)
            px = int(biome.center.x) - patch.get_width() // 2
            py = int(biome.center.y) - patch.get_height() // 2
            overlay.blit(patch, (px, py))

    return overlay
