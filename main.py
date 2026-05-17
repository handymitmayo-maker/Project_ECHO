# =============================================================================
# PROJECT ECHO – main.py
# Entry point. Initialises Pygame, runs the game loop.
# =============================================================================

import sys
import pygame

from settings import (
    WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, FPS,
    DEBUG_MODE, COLOR_BG,
)
from world import World


# =============================================================================
def main() -> None:
    # --- Pygame bootstrap ---------------------------------------------------
    pygame.init()
    pygame.display.set_caption(WINDOW_TITLE)

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock  = pygame.time.Clock()

    # Debug font (only allocated when DEBUG_MODE is True)
    debug_font = pygame.font.SysFont("Courier New", 14) if DEBUG_MODE else None

    # --- Simulation ---------------------------------------------------------
    world = World()

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

    from logger import get_logger
    get_logger().close()
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
    """Render a small HUD with simulation stats (debug mode only)."""
    lines = [
        f"FPS       : {clock.get_fps():.1f}",
        f"Tick      : {world.tick}",
        f"Creatures : {len(world.creatures)}",
        f"Food      : {len(world.foods)}",
    ]
    x, y = 10, 10
    for line in lines:
        # Shadow
        shadow = font.render(line, True, (0, 0, 0))
        screen.blit(shadow, (x + 1, y + 1))
        # Text
        text = font.render(line, True, (0, 255, 136))
        screen.blit(text, (x, y))
        y += 18


# =============================================================================
if __name__ == "__main__":
    main()
