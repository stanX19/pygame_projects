"""
Global constants and configuration for 5m War.
"""
import uuid
import pygame

# Screen & Map
# Map dimensions (in tiles)
pygame.display.init()
_MAX_SCREEN_WIDTH = pygame.display.Info().current_w
_MAX_SCREEN_HEIGHT = pygame.display.Info().current_h * 9 // 10
TILE_SIZE = 64  # Size of each tile in pixels
MAP_COLS = _MAX_SCREEN_WIDTH // TILE_SIZE
MAP_ROWS = _MAX_SCREEN_HEIGHT // TILE_SIZE

# Screen size derived from map size
SCREEN_WIDTH = MAP_COLS * TILE_SIZE
SCREEN_HEIGHT = MAP_ROWS * TILE_SIZE
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
NUM_PLAYERS = 6
MAX_UNITS = 300

# Bot Colors (Hardcoded distinct colors to avoid Player's Royal Blue)
BOT_COLORS = [
    (220, 20, 60),    # Crimson (Red-ish)
    (255, 140, 0),    # Dark Orange
    (138, 43, 226),   # Blue Violet (distinct from Royal Blue)
    (0, 128, 128),    # Teal
    (205, 20, 105),   # Deep Pink
    (139, 69, 19),    # Saddle Brown (Mountain color, but acceptable for units)
    (0, 255, 255),    # Cyan
    (50, 205, 50),    # Lime Green
    (255, 0, 255),    # Magenta
]
# Game Rules
MATCH_DURATION = 300  # 5 minutes in seconds
SUDDEN_DEATH_TIME = 240 # 4 minutes
STARTING_UNITS = 10
STARTING_RESOURCES = 50

# Map Generation
RESOURCES_PER_CASTLE = 3   # Guaranteed resources near each castle
EXTRA_RESOURCES = 0        # Random resources scattered around the map
MIN_RESOURCE_DIST = 5      # Minimum distance for extra resources from castles
CASTLE_DIST_DIFF_THRESHOLD = 3 # Max difference for castle nearest-neighbor distances

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
CASTLE_RANGE = TILE_SIZE * 2
CASTLE_CD = 0.5     # Faster attack than units relative to dmg
CASTLE_CONFIRM_TIME = 1.0       # Hold to start build
CASTLE_CONSTRUCTION_TIME = 5.0  # Time to build after confirmation


# Resource Point Stats
RES_POINT_RADIUS = 24
RES_POINT_HP = 200
RES_ATK_DMG = 5
RES_ATK_RANGE = TILE_SIZE / 2
RES_ATK_CD = 0.25
RES_GENERATION_RATE = 1.0 # Resource per second

# Physics
SEPARATION_FORCE = 500.0 # How hard units push away from each other

# Upgrade System
UPGRADE_COST_BASE = 5  # Base cost for first upgrade
UPGRADE_COST_MULTIPLIER = 1.5  # Cost multiplier per level
RANGE_UPGRADE_COST_MULTIPLIER = 10

# Max upgrade levels
MAX_UPGRADE_LEVEL = 10

# Unit Upgrades (per level bonuses)
UNIT_HP_BONUS = 5      # +5 HP per level
UNIT_DMG_BONUS = 2     # +2 damage per level
UNIT_CD_BONUS = -0.1   # -0.1s cooldown per level (faster attacks)
UNIT_SPEED_BONUS = 10  # +10 speed per level
UNIT_RANGE_BONUS = 30  # +30 range per level

# Castle Upgrades (per level bonuses)
CASTLE_HP_BONUS = 200   # HP per level
CASTLE_DMG_BONUS = 10    # damage per level
CASTLE_CD_BONUS = -CASTLE_CD / 5 # cooldown per level

# Resource Point Upgrades
RESOURCE_RATE_BONUS = 0.5  # +0.5 res/sec per level

# Castle-to-Castle Movement (global per faction)
CASTLE_MOVE_SPEED_MULTIPLIER = 3.0  # Base speed multiplier
CASTLE_MOVE_UPGRADE_BONUS = 0.5     # +0.5x multiplier per level


# path data
import os
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))