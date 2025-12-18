"""
Global constants and configuration for 5m War.
"""
import uuid

# Screen & Map
# Map dimensions (in tiles)
MAP_COLS = 20
MAP_ROWS = 10

# Screen size derived from map size
TILE_SIZE = 64  # Size of each tile in pixels
SCREEN_WIDTH = MAP_COLS * TILE_SIZE  # 25 * 64 = 1600
SCREEN_HEIGHT = MAP_ROWS * TILE_SIZE  # 15 * 64 = 960
FPS = 60

# Colors (R, G, B)
COLOR_BG = (30, 30, 30)
COLOR_PLAYER = (65, 105, 225)  # Royal Blue
COLOR_ENEMY = (220, 20, 60)    # Crimson
COLOR_NEUTRAL = (128, 128, 128)
COLOR_RESOURCE = (55, 155, 0)
COLOR_RIVER = (70, 130, 180)   # Steel Blue
COLOR_MOUNTAIN = (139, 69, 19)   # Saddle Brown
COLOR_SELECTION = (0, 255, 0)
COLOR_TEXT = (255, 255, 255)

# Faction System - Unique IDs for each faction
# Using UUID-based hashes for unique faction identification
FACTION_PLAYER = str(uuid.uuid4())[:8]
FACTION_NEUTRAL = "neutral"
NUM_PLAYERS = 4

# Bot Colors


# Game Rules
MATCH_DURATION = 300  # 5 minutes in seconds
SUDDEN_DEATH_TIME = 240 # 4 minutes
STARTING_UNITS = 10
STARTING_RESOURCES = 50

# Unit Stats
UNIT_RADIUS = 8
UNIT_SPEED = 60.0
UNIT_HP = 20
UNIT_DMG = 4
UNIT_CD = 1.0     # Attack cooldown in seconds
UNIT_COST = 1

# Castle Stats
CASTLE_RADIUS = 32
CASTLE_HP = 500
CASTLE_BUILD_COST = 10
CASTLE_BUILD_REQ = 10 # Units needed to merge
CASTLE_DMG = 10
CASTLE_RANGE = 120.0
CASTLE_CD = 0.5     # Faster attack than units relative to dmg
CASTLE_CONFIRM_TIME = 1.0       # Hold to start build
CASTLE_CONSTRUCTION_TIME = 5.0  # Time to build after confirmation


# Resource Point Stats
RES_POINT_RADIUS = 24
RES_POINT_HP = 100
RES_GENERATION_RATE = 1.0 # Resource per second

# Physics
SEPARATION_FORCE = 500.0 # How hard units push away from each other

# Upgrade System
UPGRADE_COST_BASE = 5  # Base cost for first upgrade
UPGRADE_COST_MULTIPLIER = 1.5  # Cost multiplier per level
RANGE_UPGRADE_COST_MULTIPLIER = 10

# Max upgrade levels
MAX_UPGRADE_LEVEL = 5

# Unit Upgrades (per level bonuses)
UNIT_HP_BONUS = 5      # +5 HP per level
UNIT_DMG_BONUS = 2     # +2 damage per level
UNIT_CD_BONUS = -0.1   # -0.1s cooldown per level (faster attacks)
UNIT_SPEED_BONUS = 10  # +10 speed per level
UNIT_RANGE_BONUS = 30  # +30 range per level

# Castle Upgrades (per level bonuses)
CASTLE_HP_BONUS = 100   # +100 HP per level
CASTLE_DMG_BONUS = 5    # +5 damage per level
CASTLE_CD_BONUS = -0.05 # -0.05s cooldown per level

# Resource Point Upgrades
RESOURCE_RATE_BONUS = 0.5  # +0.5 res/sec per level

# Castle-to-Castle Movement (global per faction)
CASTLE_MOVE_SPEED_MULTIPLIER = 3.0  # Base speed multiplier
CASTLE_MOVE_UPGRADE_BONUS = 0.5     # +0.5x multiplier per level