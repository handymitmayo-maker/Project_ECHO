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

# World seed (reproducible research runs vs chaotic sessions)
USE_FIXED_SEED = True         # True = RESEARCH mode, False = CHAOS mode
WORLD_SEED     = 1337         # used when USE_FIXED_SEED is True

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
COLOR_CREATURE_PARTNER = (120, 220, 255)    # soft cyan – seeking bonded partner
COLOR_BOND_LINE       = (255, 140, 200)     # faint pink glow between partners
COLOR_CORPSE          = (55,  25,  25)      # very dim – corpse
COLOR_FOOD            = (255, 60,  60)      # deep red
COLOR_BAR_BG          = (30,  30,  30)      # status bar background
COLOR_BAR_HUNGER      = (255, 100, 50)      # orange
COLOR_BAR_ENERGY      = (80,  200, 255)     # cyan
COLOR_BAR_SOCIAL      = (200, 180, 255)     # lilac
COLOR_SCANLINE        = (0,   0,   0)       # scanline overlay tint

# --- UI / HUD -----------------------------------------------------------------
SCANLINE_ALPHA        = 30          # 0–255 opacity of scanline overlay
SHOW_STATUS_BARS      = True        # [V] hunger/energy/social bars
BAR_WIDTH             = 28
BAR_HEIGHT            = 3
BAR_SPACING           = 5          # px between bar and creature edge

# HUD Panel (top-left debug overlay)
HUD_BG_COLOR          = (0,   0,   0)       # panel fill colour
HUD_BG_ALPHA          = 70                 # 0–255 panel opacity
HUD_TEXT_COLOR        = (0,   255, 136)     # phosphor green text
HUD_TEXT_SHADOW       = (0,   60,  30)      # shadow colour for depth
HUD_PADDING           = 10                  # px inner padding around text
HUD_LINE_HEIGHT       = 18                  # px between lines
HUD_FONT_SIZE         = 14                  # font size (px)

# --- Logging ------------------------------------------------------------------
LOG_TO_CONSOLE        = True        # print events to stdout
LOG_TO_FILE           = True        # write events to timestamped session file
LOG_DIR               = "logs"      # directory for session log files
LOG_FILE              = "log.txt"   # legacy alias – kept for compatibility
STATS_INTERVAL        = 5.0         # seconds between statistics dumps
SHOW_CREATURE_LABELS  = True        # [L] ECHO-NN labels above creatures
LABEL_FONT_SIZE       = 11          # px – larger = easier to read
LABEL_COLOR           = (200, 200, 200)  # bright enough to read on black bg

# --- Biomes -------------------------------------------------------------------
BIOME_COUNT          = 5
BIOME_RADIUS_MIN     = 130
BIOME_RADIUS_MAX     = 220
BIOME_FERTILE_COUNT  = 2            # number of fertile biomes
BIOME_BARREN_COUNT   = 1            # number of barren biomes (rest = neutral)
BIOME_FERTILE_RATE   = 3.0          # spawn weight multiplier
BIOME_NEUTRAL_RATE   = 1.0
BIOME_BARREN_RATE    = 0.25
BIOME_CLUSTER_STD    = 55           # px – Gaussian std for food scatter within biome
DEBUG_SHOW_BIOMES    = True         # [B] biome zone overlay

# Biome zone colours – saturated so they read clearly on grass
COLOR_BIOME_FERTILE  = (50,  210,  85)    # lush green
COLOR_BIOME_NEUTRAL  = (75,  145, 255)    # clear blue
COLOR_BIOME_BARREN   = (235,  65,  50)    # warm red

# Biome overlay (smooth radial fill – see biome_render.py)
BIOME_ALPHA_CENTER   = 100          # peak tint opacity at zone centre (0–255)
BIOME_FALLOFF        = 2.0          # >1 = softer fade toward edge
BIOME_RING_WIDTH     = 3            # px outline so each zone has a clear border
BIOME_RING_ALPHA     = 210          # outline opacity
BIOME_SHOW_LABELS    = True         # [N] zone type labels on biomes
BIOME_LABEL_FONT_SIZE = 13
COLOR_BIOME_LABEL    = (235, 245, 235)
COLOR_BIOME_LABEL_BG = (0, 0, 0, 140)

# --- Relationships ------------------------------------------------------------
REL_SOCIAL_GAIN            = 0.55   # affinity/s while actively socializing
REL_PASSIVE_GAIN           = 0.10   # affinity/s from proximity
REL_COMPETITION_LOSS        = 1.5    # affinity lost when another steals the same food
REL_RIVALRY_FLOOR          = 2.0    # skip full rivalry penalty above this affinity
REL_DECAY_RATE             = 0.004  # base affinity decay/s (slow forgetting)
REL_MEMORY_PEAK_THRESHOLD  = 3.0    # memories above this decay slower
REL_DECAY_FLOOR_FACTOR     = 0.2    # minimum decay multiplier for strong memories
REL_MUTUAL_SOCIAL_MULT     = 1.4    # gain multiplier when both socialize with each other
REL_MAX                    = 60.0
REL_MIN                    = -20.0
REL_FRIEND_THRESHOLD       = 8.0    # affinity >= this = friend
REL_FRIEND_PULL            = 0.12   # wander pull toward friends
REL_ATTRACT_MIN            = 2.0     # start attraction bias above this affinity
REL_ATTRACT_PULL           = 0.10   # wander pull scaled by affinity / REL_MAX
REL_BOND_TIERS             = (3.0, 6.0, 10.0)  # BOND_STRENGTHENED log thresholds

# --- Pair cohesion / nesting (bonded partners) --------------------------------
BOND_PARTNER_AFFINITY      = 6.0    # mutual affinity to count as bonded partners
PARTNER_SEEK_DISTANCE      = 140.0  # px – enter SEEK_PARTNER when farther apart
PARTNER_NEST_DISTANCE      = 70.0   # px – nesting comfort zone
PARTNER_REGROUP_DISTANCE   = 85.0  # px – exit SEEK_PARTNER when reunited
PARTNER_PULL_STRENGTH      = 0.28   # wander bias toward bonded partner
PARTNER_WANDER_NEAR_MULT   = 0.32  # wander perturbation scale when nested
PARTNER_WANDER_MID_MULT    = 0.55  # wander scale when within seek radius
NEST_HUNGER_RELIEF         = 0.35  # hunger decay reduction when nested
NEST_ENERGY_RATE           = 2.0   # energy/s bonus when nested with partner
PARTNER_SEEK_LOG_COOLDOWN  = 15.0  # seconds between SEEK_PARTNER logs per pair
PARTNER_REGROUP_LOG_COOLDOWN = 12.0
NEST_LOG_COOLDOWN          = 20.0  # seconds between NESTING logs per pair

# --- Social survival rewards (cooperative evolution) ----------------------------
SOCIAL_HUNGER_RELIEF       = 0.30   # hunger decay reduction while socializing with target
SOCIAL_TRUST_THRESHOLD     = 3.0    # mutual affinity for trust bonuses
SOCIAL_TRUST_ENERGY_RATE   = 2.5    # energy/s when near trusted partner
SOCIAL_TRUST_HUNGER_RELIEF = 0.15   # hunger decay reduction when near trusted partner
COOPERATIVE_LOG_COOLDOWN   = 30.0   # seconds between COOPERATIVE_SURVIVAL logs per pair

# --- Survival / Personality ---------------------------------------------------
PERS_RISK_TOLERANCE_MIN    = 0.2   # willingness to seek food at low energy
PERS_RISK_TOLERANCE_MAX    = 0.8
PERS_LAZINESS_MIN          = 0.2   # rest entry bias – higher = rests sooner / longer
PERS_LAZINESS_MAX          = 0.8
PERS_SOCIAL_DEPENDENCY_MIN = 0.2   # social entry bias – higher = socialises more readily
PERS_SOCIAL_DEPENDENCY_MAX = 0.8
PERS_FOOD_GREED_MIN        = 0.2   # perception radius boost when hungry
PERS_FOOD_GREED_MAX        = 0.8

# Energy Priority Scaling
ENERGY_SOCIAL_SUPPRESS     = 35    # below this, SOCIALIZE is suppressed
ENERGY_SURVIVAL_ONLY       = 20    # below this, only REST or nearby SEEK_FOOD allowed
ENERGY_MINIMAL_MOVE        = 10    # below this, movement is near-zero

# Smart REST
REST_ENERGY_TARGET         = 65    # creature tries to recover to this before leaving REST
REST_MIN_SOCIAL_OVERRIDE   = 0.3   # social_dependency must exceed this to exit REST for social

# Safe food-seeking distance (used when energy is critically low)
FOOD_SAFE_SEEK_RADIUS      = 220   # preferred max dist when energy < ENERGY_SURVIVAL_ONLY

# Population Pressure / Crowd Awareness
CROWD_RADIUS             = 150    # px – radius for sensing local competition density
CROWD_THRESHOLD          = 3      # min seeking creatures before pressure activates
CROWD_FOOD_SCORE_PENALTY = 50     # px added to effective food distance per nearby seeker
CROWD_WANDER_BIAS        = 0.18   # wander angle pull strength away from crowd centroid
CROWD_LOG_COOLDOWN       = 8.0    # min seconds between CROWD_AVOIDANCE logs per creature

# Food Claim System
FOOD_CLAIM_TTL             = 4.0   # seconds before an uncollected claim auto-expires
FOOD_CLAIM_OVERRIDE_FACTOR = 0.55  # creature may contest if it is ≤ this fraction of claimer distance

# Target Commitment System
TARGET_COMMIT_BASE         = 2.5   # base seconds a food/social target is held without re-evaluation
TARGET_COMMIT_VAR          = 1.5   # personality variance: risk_tolerance modulates duration
                                   #   cautious (low risk) → longer commit; reckless → shorter
TARGET_RETARGET_COOL       = 1.0   # cooldown after a voluntary target switch (prevents thrashing)
TARGET_BETTER_FACTOR       = 0.65  # only switch if new target is this fraction of current distance
                                   #   e.g. 0.65 = new target must be 35 % closer to be worth switching
CLAIM_REFRESH_INTERVAL     = 1.0   # seconds between claim TTL refreshes (not every frame)
CONTEST_LOG_COOLDOWN       = 4.0   # min seconds between FOOD_CONTEST log events per creature

# Logger anti-spam
SURVIVAL_LOG_COOLDOWN      = 6.0   # min seconds between SURVIVAL_DECISION logs per creature

# --- Reproduction (bonded pair only, intentional nesting) ---------------------
MAX_POPULATION           = 40
REPRO_AFFINITY_MIN       = 6.0     # mutual affinity – bonded partners only
REPRO_DISTANCE_MAX       = 70.0    # px – must be nested together
REPRO_ENERGY_MIN         = 60.0    # both parents must exceed
REPRO_HUNGER_MAX         = 40.0    # both parents must stay below
REPRO_AGE_MIN            = 45.0    # seconds alive (_lifespan)
REPRO_COST_ENERGY        = 40.0    # deducted from each parent on success
REPRO_COST_HUNGER        = 20.0    # added to each parent on success
REPRO_COOLDOWN           = 90.0    # per-creature cooldown after reproducing
REPRO_PAIR_COOLDOWN      = 120.0   # shared pair cooldown (world dict)
REPRO_CHECK_INTERVAL     = 2.0     # seconds between reproduction scans
REPRO_CHANCE_BASE        = 0.22    # probability after gates (scaled by affinity)
REPRO_BONDED_AFFINITY    = 6.0     # avg affinity for bonded-pair reproduction chance
REPRO_BONDED_CHANCE      = 0.40    # reproduction chance for strongly bonded pairs
REPRO_BOND_THRESHOLD     = 3.5     # mutual affinity for PAIR_BOND log
REPRO_BOND_BONUS         = 0.08    # extra chance when both are friends
REPRO_OFFSPRING_SCALE    = 0.55    # visual scale at birth
REPRO_GROWTH_DURATION    = 45.0    # seconds to reach full scale
REPRO_MUTATION_MIN       = 0.10
REPRO_MUTATION_MAX       = 0.15
REPRO_SPAWN_OFFSET       = 15.0    # random px offset from parent midpoint

# --- Background / Tiles -------------------------------------------------------
GRASS_TILE_PATH  = "grass.png"   # path to the grass tile (relative to working dir)
GRASS_TILE_DARK  = 30            # 0–255 darkness overlay on the tiled background
                                 # 0 = no darkening, 255 = fully black

# --- Debug (runtime toggles – keys in debug_controls.py) --------------------
DEBUG_MODE            = True        # [D] stats HUD
DEBUG_SHOW_PERCEPTION = True        # [P] food detection radius while seeking
DEBUG_SHOW_BOND_LINES = False       # [G] faint lines between bonded partners
DEBUG_SHOW_LINEAGE_TINT = False     # [T] subtle lineage color tint on creatures
DEBUG_SHOW_HELP       = False       # [?] control reference overlay

# --- Observer / Inspector -----------------------------------------------------
INSPECTOR_PICK_SLOP   = 8           # extra px radius for mouse picking
COLOR_SELECTION_RING  = (0, 255, 200) # cyan ring on selected creature

# =============================================================================
# Extension placeholders (filled in future versions)
# =============================================================================
# TILE_SIZE           = 32
# MAP_FILE            = "assets/map.tmx"
# EVOLUTION_ENABLED   = False
# MEMORY_LENGTH       = 20
