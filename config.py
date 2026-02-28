"""
GENESIS — Configuration Constants
All simulation parameters in one place.
"""

# ── World ────────────────────────────────────────────────────────────────
GRID_SIZE = 60
CELL_SIZE = 12            # pixels per cell
FOOD_SPAWN_RATE = 0.15    # 15% of cells start with food
FOOD_REGEN_RATE = 0.003   # per tick per cell (3x faster regrowth)
SCENT_DIFFUSION = 0.3     # how far scent spreads
SCENT_DECAY = 0.05        # scent fades per tick

# ── Energy ───────────────────────────────────────────────────────────────
ENERGY_START = 100.0
ENERGY_MAX = 150.0
ENERGY_PASSIVE_DRAIN = 0.3    # per tick just existing (reduced from 0.5)
ENERGY_MOVE_DRAIN = 0.7       # additional per tick when moving (reduced from 1.0)
ENERGY_FOOD_GAIN = 30.0       # per food eaten (increased from 20.0)

# ── Chemicals ────────────────────────────────────────────────────────────
SATIATION_DECAY = 0.02        # per tick
CURIOSITY_GAIN = 0.01         # per tick in known cell
CURIOSITY_RESET = 0.0         # when entering new cell

# ── Movement weights ────────────────────────────────────────────────────
HUNGER_WEIGHT_MULTIPLIER = 2.0
FEAR_WEIGHT_MULTIPLIER = 1.2  # softened so agents aren't paralysed by fear
CURIOSITY_WEIGHT_MULTIPLIER = 1.0
RANDOM_NOISE_RANGE = 0.1

# ── Pathway memory ──────────────────────────────────────────────────────
PATHWAY_REINFORCE = 0.1
PATHWAY_WEAKEN = 0.05
PATHWAY_WEIGHT = 0.3
PATHWAY_PRUNE_THRESHOLD = 0.01
PATHWAY_LOOKBACK = 5          # ticks to check for food reward

# ── Vision ───────────────────────────────────────────────────────────────
VISION_RANGE = 4              # cells in each direction (wider scent detection)

# ── Simulation ───────────────────────────────────────────────────────────
TARGET_FPS = 10
TICKS_PER_LOG = 100

# ── Display ──────────────────────────────────────────────────────────────
SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 780
SIDEBAR_WIDTH = 280
GRID_PIXEL_SIZE = GRID_SIZE * CELL_SIZE  # 720

# ── Seasons ──────────────────────────────────────────────────────────────
SEASON_LENGTH = 500          # ticks per season
SEASONS = ["Spring", "Summer", "Autumn", "Winter"]

SEASON_FOOD_REGEN = {
    "Spring": 0.003,
    "Summer": 0.006,
    "Autumn": 0.002,
    "Winter": 0.0003,
}
SEASON_FOOD_DECAY = {
    "Spring": 0.0,
    "Summer": 0.0,
    "Autumn": 0.0005,
    "Winter": 0.002,
}
SEASON_SCENT_DIFFUSION = {
    "Spring": 0.45,
    "Summer": 0.5,
    "Autumn": 0.35,
    "Winter": 0.2,
}
SEASON_DRAIN_MODIFIER = {
    "Spring": 1.0,
    "Summer": 0.9,
    "Autumn": 1.1,
    "Winter": 1.4,
}
SEASON_SKY_COLOR = {
    "Spring": (15, 25, 15),
    "Summer": (10, 20, 10),
    "Autumn": (25, 15, 5),
    "Winter": (10, 10, 20),
}

# ── Communication markers ────────────────────────────────────────────────
FOOD_MARKER_DECAY  = 0.005   # fades over ~200 ticks
ALARM_MARKER_DECAY = 0.01    # fades over ~100 ticks
FOOD_MARKER_WEIGHT = 1.2
ALARM_MARKER_WEIGHT = 0.8

# ── Predator ─────────────────────────────────────────────────────────────
PREDATOR_SPEED       = 3     # moves every N ticks
PREDATOR_DAMAGE      = 15.0
PREDATOR_SENSE_RANGE = 8
PREDATOR_FEAR_BOOST  = 0.4
PREDATOR_START_X     = 30
PREDATOR_START_Y     = 30

# ── Generations ──────────────────────────────────────────────────────────
INHERITANCE_STRENGTH = 0.7
MAX_GENERATIONS      = 50
