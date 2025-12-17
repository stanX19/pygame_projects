"""
Global constants and configuration for 5m War.
"""
import uuid

# Screen & Map
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TILE_SIZE = 64  # Spatial Hash cell size

# Colors (R, G, B)
COLOR_BG = (30, 30, 30)
COLOR_PLAYER = (65, 105, 225)  # Royal Blue
COLOR_ENEMY = (220, 20, 60)    # Crimson
COLOR_NEUTRAL = (128, 128, 128)
COLOR_RESOURCE = (255, 215, 0) # Gold
COLOR_RIVER = (70, 130, 180)   # Steel Blue
COLOR_MOUNTAIN = (139, 69, 19)   # Saddle Brown
COLOR_SELECTION = (0, 255, 0)
COLOR_TEXT = (255, 255, 255)

# Faction System - Unique IDs for each faction
# Using UUID-based hashes for unique faction identification
FACTION_PLAYER = str(uuid.uuid4())[:8]
FACTION_NEUTRAL = "neutral"

# Bot Colors


# Game Rules
MATCH_DURATION = 300  # 5 minutes in seconds
SUDDEN_DEATH_TIME = 240 # 4 minutes
STARTING_UNITS = 10
STARTING_RESOURCES = 5

# Unit Stats
UNIT_RADIUS = 8
UNIT_SPEED = 120.0
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