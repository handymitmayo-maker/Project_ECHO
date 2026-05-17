# =============================================================================
# PROJECT ECHO – boot_screen.py
# Atmospheric CRT-style boot sequence rendered before the simulation starts.
#
# Design goals:
#   - Delta-time-based animations (no blocking sleep() calls)
#   - Any key or ESC skips the sequence
#   - Modular phases: each phase is a simple dict describing what to show
#   - Easily extensible (new phases, sounds, lore messages)
# =============================================================================

from __future__ import annotations

import math
import random
import uuid
import datetime

import pygame

from settings import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS,
    CREATURE_COUNT, FOOD_INITIAL_COUNT, BIOME_COUNT,
)
from world_seed import boot_sidebar_seed, get_mode

# ---------------------------------------------------------------------------
# Boot constants (all tunable here)
# ---------------------------------------------------------------------------

_C_BG        = (0,   0,   0)          # background
_C_DIM       = (0,   55,  28)         # dim phosphor (hints, grid)
_C_MID       = (0,  160,  80)         # medium phosphor
_C_BRIGHT    = (0,  255, 136)         # phosphor green (main text)
_C_CYAN      = (80, 220, 220)         # accent cyan
_C_WARN      = (220, 210,  50)        # amber accent
_C_BORDER    = (0,  140,  70)         # panel border
_C_SIDEBAR_LBL = (140, 220, 170)      # sidebar field labels (readable)
_C_SIDEBAR_VAL = (0,  255, 136)       # sidebar values
_C_PANEL_BG  = (0,   18,   8, 210)    # sidebar panel fill (RGBA)

_FONT_SIZE   = 15                     # main terminal font
_TITLE_SIZE  = 36                     # PROJECT ECHO heading
_SUB_SIZE    = 13                     # sub-text / metadata
_SIDEBAR_SIZE = 14                    # sidebar metadata (slightly larger)
_LOGO_RADIUS  = 52                    # line-art emblem radius (px)

_SCANLINE_ALPHA = 25                  # scanline overlay opacity
_NOISE_ALPHA    = 12                  # static noise opacity
_FLICKER_SPEED  = 18.0                # Hz – screen brightness oscillation
_TYPING_SPEED   = 38                  # characters per second
_LINE_H         = 22                  # px between boot lines

# Phase timings (seconds)
_PHASE_BLACKOUT  = 0.35              # initial black
_PHASE_FLICKER   = 0.55              # CRT flicker-on
_PHASE_LOGO      = 1.0               # logo hold before boot lines begin
_PHASE_LINES     = None              # dynamic: depends on content
_PHASE_HOLD      = 1.8               # hold after last line
_PHASE_FADE      = 0.6               # fade to black before transition

# Boot log messages  (tag, message, optional colour override)
_BOOT_LINES: list[tuple] = [
    ("[KERNEL]",  "Initializing simulation kernel ...",           None),
    ("[WORLD]",   "Generating ecological regions ...",            None),
    ("[BIOMES]",  f"Mapping {BIOME_COUNT} biome zones ...",       _C_MID),
    ("[FOOD]",    "Spawning nutrient clusters ...",               None),
    ("[LIFE]",    f"Creating {CREATURE_COUNT} autonomous entities ...", _C_CYAN),
    ("[AI]",      "Loading behavioral matrices ...",              None),
    ("[MEMORY]",  "Initializing episodic memory structures ...",  _C_MID),
    ("[SOCIAL]",  "Linking relationship graph ...",               None),
    ("[LOGGER]",  "Starting observation archive ...",             None),
    ("[SYSTEM]",  "Observation chamber ready.",                   _C_WARN),
]

# Metadata sidebar (right column, rendered alongside boot lines)
_SESSION_ID = str(uuid.uuid4())[:8].upper()


# =============================================================================
class BootScreen:
    """
    Self-contained animated boot sequence.

    Usage
    -----
    boot = BootScreen(screen, clock)
    skipped = boot.run()   # blocks until done or skipped; returns True if skipped
    """

    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock) -> None:
        self._screen = screen
        self._clock  = clock
        self._w      = WINDOW_WIDTH
        self._h      = WINDOW_HEIGHT

        self._font       = pygame.font.SysFont("Courier New", _FONT_SIZE,  bold=False)
        self._font_b     = pygame.font.SysFont("Courier New", _FONT_SIZE,  bold=True)
        self._font_title = pygame.font.SysFont("Courier New", _TITLE_SIZE, bold=True)
        self._font_sub   = pygame.font.SysFont("Courier New", _SUB_SIZE,   bold=False)
        self._font_side  = pygame.font.SysFont("Courier New", _SIDEBAR_SIZE, bold=False)
        self._font_side_b = pygame.font.SysFont("Courier New", _SIDEBAR_SIZE, bold=True)

        self._scanline_surf = self._build_scanlines()
        self._noise_surf    = self._build_noise()

        # Phase state
        self._phase   : str   = "blackout"
        self._timer   : float = 0.0
        self._skipped : bool  = False

        # Typing animation
        self._current_line   : int   = 0       # which boot line is being typed
        self._chars_shown    : float = 0.0     # fractional chars revealed
        self._completed_lines: list[tuple] = []  # fully revealed lines

        # Fade overlay alpha (0 = transparent, 255 = black)
        self._fade_alpha: float = 0.0

        # Flicker brightness multiplier
        self._brightness: float = 1.0

        # Metadata values (animated counter-style)
        self._pop_display   = 0
        self._food_display  = 0

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def run(self) -> bool:
        """
        Run the boot sequence in a blocking loop.
        Returns True if the user skipped, False if it played fully.
        """
        running = True
        while running:
            dt = min(self._clock.tick(FPS) / 1000.0, 0.05)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    import sys; sys.exit()
                if event.type == pygame.KEYDOWN:
                    self._skipped = True
                    running = False
                    break

            if not running:
                break

            self._update(dt)
            self._draw()
            pygame.display.flip()

            if self._phase == "done":
                running = False

        return self._skipped

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def _update(self, dt: float) -> None:
        self._timer += dt

        if self._phase == "blackout":
            if self._timer >= _PHASE_BLACKOUT:
                self._next_phase("flicker")

        elif self._phase == "flicker":
            # Rapid brightness oscillation simulating CRT power-on
            self._brightness = 0.3 + 0.7 * abs(math.sin(
                self._timer * _FLICKER_SPEED * math.pi
            ))
            if self._timer >= _PHASE_FLICKER:
                self._brightness = 1.0
                self._next_phase("logo")

        elif self._phase == "logo":
            if self._timer >= _PHASE_LOGO:
                self._next_phase("lines")

        elif self._phase == "lines":
            self._update_typing(dt)

            # Animate sidebar counters
            progress = min(1.0, self._current_line / max(1, len(_BOOT_LINES)))
            self._pop_display  = int(CREATURE_COUNT  * progress)
            self._food_display = int(FOOD_INITIAL_COUNT * progress)

            if self._current_line >= len(_BOOT_LINES):
                self._next_phase("hold")

        elif self._phase == "hold":
            if self._timer >= _PHASE_HOLD:
                self._next_phase("fade")

        elif self._phase == "fade":
            self._fade_alpha = min(255, (self._timer / _PHASE_FADE) * 255)
            if self._timer >= _PHASE_FADE:
                self._next_phase("done")

    def _next_phase(self, phase: str) -> None:
        self._phase = phase
        self._timer = 0.0

    def _update_typing(self, dt: float) -> None:
        if self._current_line >= len(_BOOT_LINES):
            return

        self._chars_shown += _TYPING_SPEED * dt
        tag, msg, _ = _BOOT_LINES[self._current_line]
        full = tag + "  " + msg
        if self._chars_shown >= len(full):
            # Line complete
            self._completed_lines.append(_BOOT_LINES[self._current_line])
            self._current_line += 1
            self._chars_shown   = 0.0

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def _draw(self) -> None:
        self._screen.fill(_C_BG)

        if self._phase == "blackout":
            pygame.display.flip()
            return

        alpha = self._brightness

        # Background grid lines (subtle)
        self._draw_grid(alpha)

        # Logo area
        self._draw_logo(alpha)

        # Metadata sidebar
        self._draw_sidebar(alpha)

        # Boot lines
        self._draw_boot_lines(alpha)

        # Scanlines
        self._screen.blit(self._scanline_surf, (0, 0))

        # Noise
        self._update_noise()
        self._screen.blit(self._noise_surf, (0, 0))

        # Fade overlay (end of sequence)
        if self._fade_alpha > 0:
            fade_surf = pygame.Surface((self._w, self._h))
            fade_surf.fill(_C_BG)
            fade_surf.set_alpha(int(self._fade_alpha))
            self._screen.blit(fade_surf, (0, 0))

    def _draw_logo(self, alpha: float) -> None:
        cx = self._w // 2

        # Top separator line
        line_y = 60
        pygame.draw.line(
            self._screen, self._dim(_C_BORDER, alpha),
            (80, line_y), (self._w - 80, line_y), 1
        )

        # PROJECT ECHO title
        title = self._font_title.render("PROJECT  ECHO", True, self._dim(_C_BRIGHT, alpha))
        self._screen.blit(title, (cx - title.get_width() // 2, 72))

        # Subtitle
        sub = self._font_sub.render(
            "AUTONOMOUS LIFE SIMULATION  //  OBSERVATION FRAMEWORK v0.7",
            True, self._dim(_C_MID, alpha)
        )
        self._screen.blit(sub, (cx - sub.get_width() // 2, 118))

        # Bottom separator
        sep_y = 140
        pygame.draw.line(
            self._screen, self._dim(_C_BORDER, alpha),
            (80, sep_y), (self._w - 80, sep_y), 1
        )

    def _draw_sidebar(self, alpha: float) -> None:
        """Right column: line-art logo + readable metadata panel."""
        panel_w = 280
        panel_x = self._w - panel_w - 36
        logo_cy = 200
        meta_y  = logo_cy + _LOGO_RADIUS + 36

        # --- Line-art emblem (echo / observation motif) ---
        self._draw_line_logo(panel_x + panel_w // 2, logo_cy, _LOGO_RADIUS, alpha)

        # Wireframe "ECHO" under emblem
        self._draw_wireframe_echo(panel_x + panel_w // 2, logo_cy + _LOGO_RADIUS + 14, alpha)

        # --- Metadata panel ---
        ts = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        entries = [
            ("SESSION",    _SESSION_ID),
            ("MODE",       get_mode()),
            ("WORLD SEED", boot_sidebar_seed()),
            ("TIMESTAMP",  ts),
            ("POPULATION", str(self._pop_display)),
            ("FOOD INIT",  str(self._food_display)),
            ("BIOMES",     str(BIOME_COUNT)),
        ]
        lh      = 20
        pad     = 12
        panel_h = len(entries) * lh + pad * 2

        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pr, pg, pb, pa = _C_PANEL_BG
        panel_surf.fill((pr, pg, pb, int(pa * alpha)))
        pygame.draw.rect(
            panel_surf,
            self._dim(_C_BORDER, alpha),
            (0, 0, panel_w, panel_h), 1,
        )
        self._screen.blit(panel_surf, (panel_x, meta_y))

        y = meta_y + pad
        for label, value in entries:
            lbl = self._font_side.render(f"{label}", True, self._dim(_C_SIDEBAR_LBL, alpha))
            val = self._font_side_b.render(value, True, self._dim(_C_SIDEBAR_VAL, alpha))
            self._screen.blit(lbl, (panel_x + pad, y))
            self._screen.blit(val, (panel_x + 118, y))
            y += lh

    def _draw_line_logo(self, cx: int, cy: int, radius: int, alpha: float) -> None:
        """
        Stroke-based emblem: concentric rings, crosshair, echo arcs, corner brackets.
        Evokes sonar / observation chamber without raster graphics.
        """
        bright = self._dim(_C_BRIGHT, alpha)
        mid    = self._dim(_C_MID, alpha)
        dim    = self._dim(_C_BORDER, alpha)

        # Corner targeting brackets
        b = radius + 14
        blen = 16
        corners = [
            (cx - b, cy - b,  1,  1), (cx + b, cy - b, -1,  1),
            (cx - b, cy + b,  1, -1), (cx + b, cy + b, -1, -1),
        ]
        for px, py, sx, sy in corners:
            pygame.draw.line(self._screen, dim, (px, py), (px + sx * blen, py), 2)
            pygame.draw.line(self._screen, dim, (px, py), (px, py + sy * blen), 2)

        # Concentric rings
        pygame.draw.circle(self._screen, bright, (cx, cy), radius, 2)
        pygame.draw.circle(self._screen, mid,    (cx, cy), int(radius * 0.62), 1)
        pygame.draw.circle(self._screen, mid,    (cx, cy), int(radius * 0.32), 1)

        # Crosshair
        gap = 8
        pygame.draw.line(
            self._screen, dim,
            (cx - radius - 6, cy), (cx - gap, cy), 1,
        )
        pygame.draw.line(
            self._screen, dim,
            (cx + gap, cy), (cx + radius + 6, cy), 1,
        )
        pygame.draw.line(
            self._screen, dim,
            (cx, cy - radius - 6), (cx, cy - gap), 1,
        )
        pygame.draw.line(
            self._screen, dim,
            (cx, cy + gap), (cx, cy + radius + 6), 1,
        )

        # Echo wave arcs (right side – sound propagation)
        for i, scale in enumerate((0.45, 0.72, 1.0)):
            r = int(radius * scale)
            rect = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
            start = -math.pi / 4
            end   =  math.pi / 4
            width = 2 if i == 2 else 1
            col   = bright if i == 2 else mid
            pygame.draw.arc(self._screen, col, rect, start, end, width)

        # Pulse lines on left (incoming signal)
        for dy in (-18, 0, 18):
            x0 = cx - radius - 22
            x1 = cx - radius - 6
            pygame.draw.line(self._screen, mid, (x0, cy + dy), (x1, cy + dy), 1)

        # Core node
        pygame.draw.circle(self._screen, bright, (cx, cy), 4)
        pygame.draw.circle(self._screen, _C_BG, (cx, cy), 2)

    def _draw_wireframe_echo(self, cx: int, cy: int, alpha: float) -> None:
        """Compact ECHO lettermark built from line segments."""
        col   = self._dim(_C_BRIGHT, alpha)
        h     = 10
        w     = 7
        gap   = 4
        total = 4 * w + 3 * gap
        x0    = cx - total // 2

        def letter_e(x: int) -> None:
            pygame.draw.line(self._screen, col, (x, cy - h), (x, cy + h), 2)
            pygame.draw.line(self._screen, col, (x, cy - h), (x + w, cy - h), 2)
            pygame.draw.line(self._screen, col, (x, cy),     (x + w - 2, cy), 1)
            pygame.draw.line(self._screen, col, (x, cy + h), (x + w, cy + h), 2)

        def letter_c(x: int) -> None:
            pygame.draw.arc(
                self._screen, col,
                pygame.Rect(x, cy - h, w + 2, h * 2),
                math.pi / 2, math.pi * 1.6, 2,
            )

        def letter_h(x: int) -> None:
            pygame.draw.line(self._screen, col, (x, cy - h), (x, cy + h), 2)
            pygame.draw.line(self._screen, col, (x + w, cy - h), (x + w, cy + h), 2)
            pygame.draw.line(self._screen, col, (x, cy), (x + w, cy), 1)

        def letter_o(x: int) -> None:
            pygame.draw.rect(
                self._screen, col,
                pygame.Rect(x, cy - h, w, h * 2), 2,
            )

        letter_e(x0)
        letter_c(x0 + w + gap)
        letter_h(x0 + 2 * (w + gap))
        letter_o(x0 + 3 * (w + gap))

    def _draw_boot_lines(self, alpha: float) -> None:
        if self._phase not in ("lines", "hold", "fade"):
            return

        x = 90
        y = 165
        lh = _LINE_H

        # Completed lines
        for tag, msg, col_override in self._completed_lines:
            col = col_override if col_override else _C_BRIGHT
            tag_surf = self._font_b.render(tag + "  ", True, self._dim(_C_MID, alpha))
            msg_surf = self._font.render(msg,           True, self._dim(col, alpha))
            self._screen.blit(tag_surf, (x, y))
            self._screen.blit(msg_surf, (x + tag_surf.get_width(), y))
            y += lh

        # Currently typing line
        if self._current_line < len(_BOOT_LINES):
            tag, msg, col_override = _BOOT_LINES[self._current_line]
            col  = col_override if col_override else _C_BRIGHT
            full = tag + "  " + msg
            visible = full[: int(self._chars_shown)]

            # Split visible into tag portion and msg portion
            tag_full = tag + "  "
            if len(visible) <= len(tag_full):
                tag_vis = visible
                msg_vis = ""
            else:
                tag_vis = tag_full
                msg_vis = visible[len(tag_full):]

            tag_surf = self._font_b.render(tag_vis, True, self._dim(_C_MID, alpha))
            msg_surf = self._font.render(msg_vis,   True, self._dim(col, alpha))
            self._screen.blit(tag_surf, (x, y))
            self._screen.blit(msg_surf, (x + tag_surf.get_width(), y))

            # Blinking cursor
            if int(pygame.time.get_ticks() / 400) % 2 == 0:
                cx = x + tag_surf.get_width() + msg_surf.get_width() + 2
                pygame.draw.rect(
                    self._screen,
                    self._dim(_C_BRIGHT, alpha),
                    (cx, y + 2, 8, _FONT_SIZE - 2),
                )
            y += lh

        # Progress bar at bottom
        self._draw_progress_bar(alpha, y + 10)

        # Skip hint
        hint = self._font_sub.render(
            "[ PRESS ANY KEY TO SKIP ]", True, self._dim(_C_MID, alpha)
        )
        self._screen.blit(
            hint, (self._w // 2 - hint.get_width() // 2, self._h - 30)
        )

    def _draw_progress_bar(self, alpha: float, y: int) -> None:
        total    = len(_BOOT_LINES)
        progress = min(1.0, self._current_line / total)
        bar_x    = 90
        bar_w    = self._w - 400
        bar_h    = 3

        # Background track
        pygame.draw.rect(
            self._screen, self._dim(_C_DIM, alpha),
            (bar_x, y, bar_w, bar_h)
        )
        # Filled portion
        filled = int(bar_w * progress)
        if filled > 0:
            pygame.draw.rect(
                self._screen, self._dim(_C_BRIGHT, alpha),
                (bar_x, y, filled, bar_h)
            )
        # Percentage label
        pct = self._font_sub.render(
            f"{int(progress * 100):3d}%", True, self._dim(_C_MID, alpha)
        )
        self._screen.blit(pct, (bar_x + bar_w + 8, y - 4))

    def _draw_grid(self, alpha: float) -> None:
        """Subtle background grid for CRT depth."""
        spacing = 40
        col     = self._dim(_C_DIM, alpha * 0.25)
        for x in range(0, self._w, spacing):
            pygame.draw.line(self._screen, col, (x, 0), (x, self._h))
        for y in range(0, self._h, spacing):
            pygame.draw.line(self._screen, col, (0, y), (self._w, y))

    # ------------------------------------------------------------------
    # Surface builders
    # ------------------------------------------------------------------

    def _build_scanlines(self) -> pygame.Surface:
        surf = pygame.Surface((self._w, self._h), pygame.SRCALPHA)
        for y in range(0, self._h, 3):
            pygame.draw.line(surf, (0, 0, 0, _SCANLINE_ALPHA), (0, y), (self._w, y))
        return surf

    def _build_noise(self) -> pygame.Surface:
        surf = pygame.Surface((self._w, self._h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        return surf

    def _update_noise(self) -> None:
        """Randomise a sparse set of pixels each frame to simulate CRT static."""
        self._noise_surf.fill((0, 0, 0, 0))
        for _ in range(200):
            nx = random.randint(0, self._w - 1)
            ny = random.randint(0, self._h - 1)
            br = random.randint(0, 180)
            self._noise_surf.set_at((nx, ny), (br, min(255, br + 60), br, _NOISE_ALPHA + random.randint(0, 20)))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _dim(color: tuple, alpha: float) -> tuple:
        """Scale an RGB colour by alpha (0.0–1.0) for brightness effects."""
        return (
            int(color[0] * alpha),
            int(color[1] * alpha),
            int(color[2] * alpha),
        )
