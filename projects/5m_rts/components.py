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
    shape: str  # 'circle', 'square', 'triangle'
    layer: int = 1 # 0: terrain, 1: units, 2: ui

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