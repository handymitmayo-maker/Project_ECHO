# =============================================================================
# PROJECT ECHO – main.py
# Entry point. Initialises Pygame, runs the game loop.
# =============================================================================

import sys
import pygame

from settings import (
    WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, FPS,
    HUD_BG_COLOR, HUD_BG_ALPHA, HUD_TEXT_COLOR, HUD_TEXT_SHADOW,
    HUD_PADDING, HUD_LINE_HEIGHT, HUD_FONT_SIZE,
)
import settings
from boot_screen import BootScreen
from debug_controls import handle_key, help_lines, is_on, status_lines
from world import World


# =============================================================================
def main() -> None:
    # --- Pygame bootstrap ---------------------------------------------------
    pygame.init()
    pygame.display.set_caption(WINDOW_TITLE)

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock  = pygame.time.Clock()

    hud_font = pygame.font.SysFont("Courier New", HUD_FONT_SIZE)

    # --- Boot screen --------------------------------------------------------
    BootScreen(screen, clock).run()

    # --- Simulation ---------------------------------------------------------
    world = World()

    from logger import get_logger
    get_logger().start_session(world)

    # --- Game loop ----------------------------------------------------------
    running = True
    while running:

        # 1. Fixed-rate delta time (capped to avoid spiral of death)
        dt = min(clock.tick(FPS) / 1000.0, 0.05)

        # 2. Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                _handle_keydown(event, world)

        # 3. Simulation update
        world.update(dt)

        # 4. Render
        world.draw(screen)

        if is_on("DEBUG_MODE"):
            _draw_debug_hud(screen, hud_font, clock, world)

        if settings.DEBUG_SHOW_HELP:
            _draw_help_overlay(screen, hud_font)

        pygame.display.flip()

    get_logger().close(world)
    pygame.quit()
    sys.exit()


# =============================================================================
def _handle_keydown(event: pygame.event.Event, world: World) -> None:
    """
    Keyboard controls.

    ESC     – quit
    ?       – toggle help overlay (lists all debug keys)
    D/B/N/P/L/V – debug toggles (see debug_controls.py)
    SPACE   – spawn food burst
    """
    if event.key == pygame.K_ESCAPE:
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        return

    if event.key == pygame.K_QUESTION or event.key == pygame.K_SLASH:
        settings.DEBUG_SHOW_HELP = not settings.DEBUG_SHOW_HELP
        return

    if handle_key(event.key, world):
        return

    if event.key == pygame.K_SPACE:
        import random
        from food import Food
        cx = random.uniform(100, settings.WORLD_WIDTH  - 100)
        cy = random.uniform(100, settings.WORLD_HEIGHT - 100)
        for _ in range(8):
            fx = cx + random.uniform(-60, 60)
            fy = cy + random.uniform(-60, 60)
            world.foods.append(Food(fx, fy))


# =============================================================================
def _draw_panel(
    screen: pygame.Surface,
    font: pygame.font.Font,
    lines: list[str],
    x: int,
    y: int,
) -> None:
    """Shared semi-transparent HUD panel renderer."""
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


def _draw_debug_hud(
    screen: pygame.Surface,
    font: pygame.font.Font,
    clock: pygame.time.Clock,
    world: World,
) -> None:
    """Top-left stats + live toggle states."""
    alive = [c for c in world.creatures if c.alive]
    lines = [
        f"FPS       : {clock.get_fps():.1f}",
        f"Tick      : {world.tick}",
        f"Creatures : {len(alive)}",
        f"Food      : {len(world.foods)}",
        "---",
        *status_lines(),
        "[?] Help",
    ]
    if is_on("DEBUG_SHOW_BIOMES"):
        for b in world.biomes:
            lines.append(f"  {b.type:7} r={int(b.radius):3}  ({int(b.center.x)},{int(b.center.y)})")

    _draw_panel(screen, font, lines, 8, 8)


def _draw_help_overlay(screen: pygame.Surface, font: pygame.font.Font) -> None:
    """Bottom-right control reference."""
    lines = help_lines()
    text_w = max(font.size(line)[0] for line in lines)
    pad = HUD_PADDING
    x = WINDOW_WIDTH - text_w - pad * 2 - 12
    y = WINDOW_HEIGHT - HUD_LINE_HEIGHT * len(lines) - pad * 2 - 12
    _draw_panel(screen, font, lines, x, y)


# =============================================================================
if __name__ == "__main__":
    main()
