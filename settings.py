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

HUNGER_DECAY_RATE     = 4.0         # hunger units per second (always)
ENERGY_DECAY_RATE     = 2.0         # legacy alias – no longer used directly
ENERGY_DECAY_WANDER   = 1.2         # energy cost while WANDER / SOCIALIZE
ENERGY_DECAY_SEEK     = 2.8         # energy cost while SEEK_FOOD (urgency costs)
ENERGY_REST_RATE      = 18.0        # energy gained per second while REST (was 12)
SOCIAL_DECAY_RATE     = 1.5         # social units lost per second (alone)
SOCIAL_GAIN_RATE      = 8.0         # social units gained per second (near others)

# Food perception
FOOD_DETECTION_RADIUS        = 200  # px – normal perception range
FOOD_DETECTION_RADIUS_HUNGRY = 280  # px – expanded range when very hungry
FOOD_HUNGER_SCAN_BOOST       = 70   # hunger above this activates larger radius
FOOD_MEMORY_DURATION         = 8.0  # seconds the last known food position is remembered

# State commitment (anti-thrashing)
STATE_MIN_DURATION     = 2.0        # min seconds in any state before voluntary switch
STATE_EMERGENCY_HUNGER = 80         # hunger above this overrides commitment immediately

# Hysteresis thresholds – separate enter vs exit values prevent rapid oscillation
HUNGER_SEEK_ENTER      = 55         # enter SEEK_FOOD when hunger > this
HUNGER_SEEK_EXIT       = 35         # leave SEEK_FOOD only when hunger drops below this
ENERGY_REST_ENTER      = 25         # enter REST when energy < this
ENERGY_REST_EXIT       = 45         # leave REST only when energy recovers above this
SOCIAL_ENTER           = 30         # enter SOCIALIZE when social < this
SOCIAL_EXIT            = 50         # leave SOCIALIZE only when social > this

# Legacy aliases – kept so logger.py import of HUNGER_THRESHOLD still resolves
HUNGER_THRESHOLD      = HUNGER_SEEK_ENTER
ENERGY_THRESHOLD      = ENERGY_REST_ENTER
SOCIAL_THRESHOLD      = SOCIAL_ENTER

SOCIAL_RADIUS         = 120         # px radius for detecting nearby creatures

# Dying / death
DYING_ENERGY_THRESHOLD = 12         # enter DYING when energy < this
DYING_HUNGER_THRESHOLD = 88         # enter DYING when hunger > this
DEATH_CRITICAL_TIME    = 6.0        # seconds at energy==0 or hunger==100 before death

# Corpse
CORPSE_DURATION        = 6.0        # seconds corpse remains visible before removal

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
COLOR_CREATURE_DYING  = (180, 50,  50)      # dim red – dying
COLOR_CORPSE          = (55,  25,  25)      # very dim – corpse
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

# --- Logging ------------------------------------------------------------------
LOG_TO_CONSOLE        = True        # print events to stdout
LOG_TO_FILE           = True        # write events to log.txt
LOG_FILE              = "log.txt"   # relative to working directory
STATS_INTERVAL        = 5.0         # seconds between statistics dumps
SHOW_CREATURE_LABELS  = True        # render ECHO-NN label above each creature
LABEL_FONT_SIZE       = 11          # px – larger = easier to read
LABEL_COLOR           = (200, 200, 200)  # bright enough to read on black bg

# --- Debug --------------------------------------------------------------------
DEBUG_MODE            = False       # show extra info when True
DEBUG_SHOW_PERCEPTION = True       # draw food-perception radius on SEEK_FOOD creatures

# =============================================================================
# Extension placeholders (filled in future versions)
# =============================================================================
# TILE_SIZE           = 32
# MAP_FILE            = "assets/map.tmx"
# EVOLUTION_ENABLED   = False
# MEMORY_LENGTH       = 20
