# =============================================================================
# PROJECT ECHO – settings.py
# Central configuration. All tunable constants live here.
# =============================================================================

# --- Window -------------------------------------------------------------------
WINDOW_TITLE  = "PROJECT ECHO"
WINDOW_WIDTH  = 1280
WINDOW_HEIGHT = 720
FPS           = 60

# --- World --------------------------------------------------------------------
WORLD_WIDTH   = WINDOW_WIDTH
WORLD_HEIGHT  = WINDOW_HEIGHT

# --- Creature -----------------------------------------------------------------
CREATURE_COUNT        = 12          # initial population
CREATURE_RADIUS       = 6           # visual size (px)
CREATURE_SPEED        = 35          # max pixels/second (was 80)
CREATURE_SPEED_MIN    = 20          # personality lower bound
CREATURE_SPEED_MAX    = 48          # personality upper bound
CREATURE_ARRIVE_RADIUS = 50         # slow-down distance for Arrive steering (was 20)

# Steering / physics
CREATURE_ACCEL_FACTOR = 0.04        # lerp factor toward desired vel per frame (was 0.15)
CREATURE_FRICTION     = 2.5         # velocity drag applied as vel *= (1 - friction*dt)

# Wander (Reynolds Wander Circle)
WANDER_CIRCLE_DIST    = 60          # px ahead to project the wander circle centre
WANDER_CIRCLE_RADIUS  = 35          # radius of the wander circle
WANDER_ANGLE_SPEED    = 1.4         # max rad/s the wander angle can change per second
WANDER_CHANGE_INTERVAL = 4.5        # seconds between idle-chance rolls (was 2.5)

# Idle
IDLE_CHANCE           = 0.35        # probability of an idle pause at each interval
IDLE_DURATION_MIN     = 1.5         # seconds
IDLE_DURATION_MAX     = 5.0         # seconds

HUNGER_DECAY_RATE     = 4.0         # hunger units lost per second
ENERGY_DECAY_RATE     = 2.0         # energy units lost per second (while moving)
ENERGY_REST_RATE      = 12.0        # energy units gained per second (while resting)
SOCIAL_DECAY_RATE     = 1.5         # social units lost per second (alone)
SOCIAL_GAIN_RATE      = 8.0         # social units gained per second (near others)

HUNGER_THRESHOLD      = 55          # hunger > this  → SEEK_FOOD
ENERGY_THRESHOLD      = 25          # energy < this  → REST
SOCIAL_THRESHOLD      = 30          # social < this  → SOCIALIZE

SOCIAL_RADIUS         = 120         # px radius for detecting nearby creatures

# --- Food ---------------------------------------------------------------------
FOOD_INITIAL_COUNT    = 20          # food items at game start
FOOD_NUTRITION        = 35          # hunger units restored on eat
FOOD_RADIUS           = 4           # visual size (px)
FOOD_SPAWN_INTERVAL   = 3.0         # seconds between automatic food spawns
FOOD_SPAWN_BATCH      = 3           # food items spawned each interval
FOOD_MAX_COUNT        = 60          # hard cap on simultaneous food items

# --- Colors (retro / phosphor palette) ----------------------------------------
COLOR_BG              = (0,   0,   0)       # deep black
COLOR_CREATURE        = (0,   255, 136)     # phosphor green
COLOR_CREATURE_REST   = (0,   180, 255)     # ice blue – resting
COLOR_CREATURE_SOCIAL = (255, 220, 0)       # amber – socialising
COLOR_CREATURE_SEEK   = (255, 80,  80)      # alert red – hungry
COLOR_FOOD            = (255, 60,  60)      # deep red
COLOR_BAR_BG          = (30,  30,  30)      # status bar background
COLOR_BAR_HUNGER      = (255, 100, 50)      # orange
COLOR_BAR_ENERGY      = (80,  200, 255)     # cyan
COLOR_BAR_SOCIAL      = (200, 180, 255)     # lilac
COLOR_SCANLINE        = (0,   0,   0)       # scanline overlay tint

# --- UI / HUD -----------------------------------------------------------------
SCANLINE_ALPHA        = 30          # 0–255 opacity of scanline overlay
SHOW_STATUS_BARS      = True        # toggle creature status bars
BAR_WIDTH             = 28
BAR_HEIGHT            = 3
BAR_SPACING           = 5          # px between bar and creature edge

# --- Debug --------------------------------------------------------------------
DEBUG_MODE            = False       # show extra info when True

# =============================================================================
# Extension placeholders (filled in future versions)
# =============================================================================
# TILE_SIZE           = 32
# MAP_FILE            = "assets/map.tmx"
# EVOLUTION_ENABLED   = False
# MEMORY_LENGTH       = 20
