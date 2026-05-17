# =============================================================================
# PROJECT ECHO – food.py
# Food entity. Kreaturen fressen es; danach wird es entfernt.
# =============================================================================

import pygame
from settings import (
    FOOD_NUTRITION, FOOD_RADIUS,
    COLOR_FOOD, COLOR_BAR_BG,
)


class Food:
    """A single food item placed in the world."""

    def __init__(self, x: float, y: float) -> None:
        self.pos       = pygame.Vector2(x, y)
        self.nutrition = FOOD_NUTRITION
        self.radius    = FOOD_RADIUS
        self.alive     = True           # set False when eaten; World removes it

        # Pulse animation state
        self._pulse_t  = 0.0

    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        """Animate the food (gentle pulse)."""
        self._pulse_t += dt * 2.5

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        """Draw a pulsing dot at self.pos."""
        import math
        pulse  = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(self._pulse_t))
        radius = max(1, round(self.radius * pulse))

        # Soft glow: larger, dimmer circle behind
        glow_color  = (
            min(255, COLOR_FOOD[0] + 40),
            min(255, COLOR_FOOD[1] + 20),
            min(255, COLOR_FOOD[2] + 20),
        )
        glow_surf = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
        pygame.draw.circle(
            glow_surf,
            (*glow_color, 60),
            (radius * 2, radius * 2),
            radius * 2,
        )
        surface.blit(
            glow_surf,
            (int(self.pos.x) - radius * 2, int(self.pos.y) - radius * 2),
        )

        # Core dot
        pygame.draw.circle(
            surface,
            COLOR_FOOD,
            (int(self.pos.x), int(self.pos.y)),
            radius,
        )

    # ------------------------------------------------------------------
    def __repr__(self) -> str:
        return f"Food(pos={self.pos}, nutrition={self.nutrition}, alive={self.alive})"
