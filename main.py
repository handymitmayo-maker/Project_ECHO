# =============================================================================
# PROJECT ECHO – main.py
# Entry point. Initialises Pygame, runs the game loop.
# =============================================================================

import sys
import pygame

from settings import (
    WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, FPS,
    HUD_FONT_SIZE,
)
import settings
from world_seed import init_world_seed, reseed_world_rng
from boot_screen import BootScreen
from debug_controls import handle_key, help_lines, is_on, status_lines, dump_rng
from observer import SimulationObserver
from ui_panels import draw_panel
from world import World


# =============================================================================
def main() -> None:
    # --- Pygame bootstrap ---------------------------------------------------
    pygame.init()
    pygame.display.set_caption(WINDOW_TITLE)

    # Seed RNG before boot UI randomness and world generation
    init_world_seed()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock  = pygame.time.Clock()

    hud_font = pygame.font.SysFont("Courier New", HUD_FONT_SIZE)

    # --- Boot screen --------------------------------------------------------
    BootScreen(screen, clock).run()

    # --- Simulation ---------------------------------------------------------
    reseed_world_rng()
    world = World()

    from logger import get_logger
    get_logger().start_session(world)

    observer = SimulationObserver()

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
                if not _handle_keydown(event, world, observer):
                    pass
            elif observer.handle_event(event, world):
                pass

        # 3. Simulation update
        if not observer.frozen:
            world.update(dt)
        observer.update(dt, world)

        # 4. Render
        world.draw(screen)
        observer.draw_overlays(screen, world)

        if is_on("DEBUG_MODE"):
            _draw_debug_hud(screen, hud_font, clock, world, observer)

        observer.draw_inspector(screen, world)

        if settings.DEBUG_SHOW_HELP:
            _draw_help_overlay(screen, hud_font)

        pygame.display.flip()

    get_logger().close(world)
    pygame.quit()
    sys.exit()


# =============================================================================
def _handle_keydown(
    event: pygame.event.Event,
    world: World,
    observer: SimulationObserver,
) -> bool:
    """
    Keyboard controls. Returns True if handled.

    ESC     – quit
    ?       – toggle help overlay
    D/B/N/P/L/V/G/T – debug toggles
    H       – RNG / world hash dump
    F       – freeze (observer)
    I       – profile dump (observer)
    SPACE   – spawn food burst
    """
    if event.key == pygame.K_ESCAPE:
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        return True

    if event.key == pygame.K_QUESTION or event.key == pygame.K_SLASH:
        settings.DEBUG_SHOW_HELP = not settings.DEBUG_SHOW_HELP
        return True

    if event.key == pygame.K_h:
        dump_rng(world)
        return True

    if observer.handle_event(event, world):
        return True

    if handle_key(event.key, world):
        return True

    if event.key == pygame.K_SPACE:
        import random
        from food import Food
        cx = random.uniform(100, settings.WORLD_WIDTH  - 100)
        cy = random.uniform(100, settings.WORLD_HEIGHT - 100)
        for _ in range(8):
            fx = cx + random.uniform(-60, 60)
            fy = cy + random.uniform(-60, 60)
            world.foods.append(Food(fx, fy))
        return True

    return False


# =============================================================================
def _draw_debug_hud(
    screen: pygame.Surface,
    font: pygame.font.Font,
    clock: pygame.time.Clock,
    world: World,
    observer: SimulationObserver,
) -> None:
    """Top-left stats + live toggle states."""
    alive = [c for c in world.creatures if c.alive]
    lines = [
        f"FPS       : {clock.get_fps():.1f}",
        f"Tick      : {world.tick}",
        f"Creatures : {len(alive)}",
        f"Food      : {len(world.foods)}",
        f"World hash: {world.initial_hash}",
        f"Frozen    : {'ON' if observer.frozen else 'off'}",
        f"Selected  : {observer.selected.label if observer.selected else 'none'}",
        "---",
        *status_lines(),
        "[?] Help",
    ]
    if is_on("DEBUG_SHOW_BIOMES"):
        for b in world.biomes:
            lines.append(f"  {b.type:7} r={int(b.radius):3}  ({int(b.center.x)},{int(b.center.y)})")

    draw_panel(screen, font, lines, 8, 8)


def _draw_help_overlay(screen: pygame.Surface, font: pygame.font.Font) -> None:
    """Bottom-right control reference."""
    lines = help_lines()
    text_w = max(font.size(line)[0] for line in lines)
    pad = 10
    x = WINDOW_WIDTH - text_w - pad * 2 - 12
    y = WINDOW_HEIGHT - 18 * len(lines) - pad * 2 - 12
    draw_panel(screen, font, lines, x, y)


# =============================================================================
if __name__ == "__main__":
    main()
