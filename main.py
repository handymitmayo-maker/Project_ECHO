# =============================================================================
# PROJECT ECHO – main.py
# Entry point. Initialises Pygame, runs the game loop.
# =============================================================================

import sys
import pygame

from settings import (
    WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, FPS,
    DEBUG_MODE, COLOR_BG,
    HUD_BG_COLOR, HUD_BG_ALPHA, HUD_TEXT_COLOR, HUD_TEXT_SHADOW,
    HUD_PADDING, HUD_LINE_HEIGHT, HUD_FONT_SIZE,
)
from boot_screen import BootScreen
from world import World


# =============================================================================
def main() -> None:
    # --- Pygame bootstrap ---------------------------------------------------
    pygame.init()
    pygame.display.set_caption(WINDOW_TITLE)

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock  = pygame.time.Clock()

    # Debug font (only allocated when DEBUG_MODE is True)
    debug_font = pygame.font.SysFont("Courier New", HUD_FONT_SIZE) if DEBUG_MODE else None

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

        if DEBUG_MODE and debug_font:
            _draw_debug(screen, debug_font, clock, world)

        pygame.display.flip()

    get_logger().close(world)
    pygame.quit()
    sys.exit()


# =============================================================================
def _handle_keydown(event: pygame.event.Event, world: "World") -> None:
    """
    Keyboard controls.

    ESC     – quit
    D       – toggle DEBUG_MODE at runtime
    SPACE   – spawn a burst of food manually
    """
    import settings  # local import so we can mutate the module-level flag

    if event.key == pygame.K_ESCAPE:
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    elif event.key == pygame.K_d:
        settings.DEBUG_MODE = not settings.DEBUG_MODE

    elif event.key == pygame.K_SPACE:
        # Manual food drop at a random cluster position
        import random
        from food import Food
        cx = random.uniform(100, settings.WORLD_WIDTH  - 100)
        cy = random.uniform(100, settings.WORLD_HEIGHT - 100)
        for _ in range(8):
            fx = cx + random.uniform(-60, 60)
            fy = cy + random.uniform(-60, 60)
            world.foods.append(Food(fx, fy))


# =============================================================================
def _draw_debug(
    screen     : pygame.Surface,
    font       : pygame.font.Font,
    clock      : pygame.time.Clock,
    world      : "World",
) -> None:
    """Render a semi-transparent HUD panel with simulation stats."""
    alive = [c for c in world.creatures if c.alive]
    lines = [
        f"FPS       : {clock.get_fps():.1f}",
        f"Tick      : {world.tick}",
        f"Creatures : {len(alive)}",
        f"Food      : {len(world.foods)}",
    ]

    pad     = HUD_PADDING
    text_w  = max(font.size(line)[0] for line in lines)
    text_h  = HUD_LINE_HEIGHT * len(lines)
    panel_w = text_w + pad * 2
    panel_h = text_h + pad * 2

    # Semi-transparent dark panel
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((*HUD_BG_COLOR, HUD_BG_ALPHA))
    screen.blit(panel, (8, 8))

    # Text with drop shadow
    x = 8 + pad
    y = 8 + pad
    for line in lines:
        shadow = font.render(line, True, HUD_TEXT_SHADOW)
        screen.blit(shadow, (x + 1, y + 1))
        text = font.render(line, True, HUD_TEXT_COLOR)
        screen.blit(text, (x, y))
        y += HUD_LINE_HEIGHT


# =============================================================================
if __name__ == "__main__":
    main()
