"""
Data Component definitions for the Esper ECS.
Pure data classes, no logic.
"""
import dataclasses
from typing import Tuple, List

@dataclasses.dataclass
class Transform:
    x: float
    y: float
    radius: float = 8.0

@dataclasses.dataclass
class Velocity:
    vx: float = 0.0
    vy: float = 0.0

@dataclasses.dataclass
class Renderable:
    color: Tuple[int, int, int]
    shape: str  # 'circle', 'square', 'triangle', 'polygon'
    layer: int = 1 # 0: terrain, 1: units, 2: ui
    polygon_points: List[Tuple[float, float]] = None  # Custom polygon points for upgraded units

@dataclasses.dataclass
class Identity:
    faction: str  # uuid string
    type: str     # 'unit', 'castle', 'resource', 'obstacle'

@dataclasses.dataclass
class Stats:
    hp: int
    max_hp: int
    attack_dmg: int
    attack_range: float
    attack_cd: float
    current_cd: float = 0.0
    dead: bool = False

@dataclasses.dataclass
class Movement:
    speed: float
    target_x: float = None
    target_y: float = None
    path: List[Tuple[float, float]] = dataclasses.field(default_factory=list)
    moving: bool = False
    is_castle_to_castle: bool = False  # For special movement speed

@dataclasses.dataclass
class Selectable:
    selected: bool = False

@dataclasses.dataclass
class ResourceGenerator:
    rate: float
    accumulated: float = 0.0

@dataclasses.dataclass
class ConstructionSite:
    total_time: float
    elapsed: float
    units_ids: List[int]
    faction: str

@dataclasses.dataclass
class AIController:
    active: bool = True
    auto_spawn: bool = True
    auto_attack: bool = True

@dataclasses.dataclass
class FactionInfo:
    id: str
    name: str
    color: Tuple[int, int, int]

@dataclasses.dataclass
class Upgrades:
    """Track upgrade levels for individual entities (units, castles, resource points)"""
    hp_level: int = 0
    dmg_level: int = 0
    cd_level: int = 0
    speed_level: int = 0  # For units
    rate_level: int = 0   # For resource points
    range_level: int = 0  # For attack range

@dataclasses.dataclass
class FactionUpgrades:
    """Track faction-wide upgrades"""
    faction_id: str
    castle_move_level: int = 0  # Castle-to-castle movement speed upgrade

@dataclasses.dataclass
class Projectile:
    """Visual projectile for ranged attacks"""
    start_x: float
    start_y: float
    target_x: float
    target_y: float
    speed: float = 500.0  # Pixels per second
    damage: int = 0  # Damage to deal on impact
    target_entity: int = None  # Target entity ID
    attacker_faction: str = None  # Faction that fired this projectile
    lifetime: float = 0.0  # Time alive
    max_lifetime: float = 2.0  # Max time before despawn

@dataclasses.dataclass
class KillRequest:
    """Request to kill/capture an entity - processed by CleanupSystem"""
    killer_faction: str  # Faction that killed this entity
    killed_entity: int  # Entity ID that was killed