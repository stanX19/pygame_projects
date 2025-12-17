"""
Entry point for 5m War.
"""
import pygame
import esper
import sys
from config import *
from components import *
from systems import *
from spatial_hash import SpatialHash
import collections

class SceneManager:
    def __init__(self):
        self.world = esper.World()
        self.world.scene_manager = self # Inject ref

        self.dt = 0.016
        self.game_time = 0.0
        self.resources = {FACTION_PLAYER: STARTING_RESOURCES}
        self.sudden_death = False
        self.events = []
        self.events = []
        self.game_over = False
        self.winner = None  # Will be set to winning faction ID
        self.player_faction_id = FACTION_PLAYER  # Track which faction is the player
        
        self.message = ""
        self.message_color = (255, 255, 255)
        self.message_timer = 0.0
        
        # Utils
        self.spatial_hash = SpatialHash(TILE_SIZE)
        
        # Pathfinding Grid (0: Walkable, 1: Blocked)
        self.cols = (SCREEN_WIDTH // TILE_SIZE) + 1
        self.rows = (SCREEN_HEIGHT // TILE_SIZE) + 1
        self.grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        
        # Upgrade tracking per faction
        self.faction_upgrades = {}  # faction_id -> {upgrade_type: level}

    def mark_obstacle(self, x, y, radius):
        """Mark all grid cells covered by an obstacle with given radius."""
        # Calculate the bounding box of the obstacle in grid coordinates
        # Add a small buffer to ensure proper blocking
        buffer = 8  # Extra pixels to ensure blocking
        min_x = int((x - radius - buffer) // TILE_SIZE)
        max_x = int((x + radius + buffer) // TILE_SIZE)
        min_y = int((y - radius - buffer) // TILE_SIZE)
        max_y = int((y + radius + buffer) // TILE_SIZE)
        
        # Mark all cells in the bounding box
        for cy in range(min_y, max_y + 1):
            for cx in range(min_x, max_x + 1):
                if 0 <= cy < self.rows and 0 <= cx < self.cols:
                    # Check if cell center is within obstacle radius
                    cell_center_x = cx * TILE_SIZE + TILE_SIZE / 2
                    cell_center_y = cy * TILE_SIZE + TILE_SIZE / 2
                    dist = math.hypot(cell_center_x - x, cell_center_y - y)
                    # Mark as blocked if cell center is within radius + buffer
                    if dist <= radius + buffer:
                        self.grid[cy][cx] = 1

    def show_message(self, text, color=(255, 255, 255), duration=2.0):
        self.message = text
        self.message_color = color
        self.message_timer = duration

    def get_faction_color(self, faction_id):
        for ent, info in self.world.get_component(FactionInfo):
            if info.id == faction_id:
                return info.color
        return COLOR_NEUTRAL
    
    def init_faction_upgrades(self, faction_id):
        """Initialize upgrade tracking for a faction"""
        self.faction_upgrades[faction_id] = {
            'unit_hp': 0,
            'unit_dmg': 0,
            'unit_cd': 0,
            'unit_speed': 0,
            'unit_range': 0,
            'castle_hp': 0,
            'castle_dmg': 0,
            'castle_cd': 0,
            'resource_rate': 0,
            'castle_move': 0
        }
    
    def apply_faction_upgrades_to_entity(self, ent, faction_id, entity_type):
        """Apply current faction upgrade levels to a newly created entity"""
        if faction_id not in self.faction_upgrades:
            return
        
        upgrades = Upgrades()
        
        if entity_type == 'unit':
            upgrades.hp_level = self.faction_upgrades[faction_id]['unit_hp']
            upgrades.dmg_level = self.faction_upgrades[faction_id]['unit_dmg']
            upgrades.cd_level = self.faction_upgrades[faction_id]['unit_cd']
            upgrades.speed_level = self.faction_upgrades[faction_id]['unit_speed']
            upgrades.range_level = self.faction_upgrades[faction_id]['unit_range']
            
            # Apply bonuses to stats
            stats = self.world.component_for_entity(ent, Stats)
            stats.max_hp = UNIT_HP + (UNIT_HP_BONUS * upgrades.hp_level)
            stats.hp = stats.max_hp
            stats.attack_dmg = UNIT_DMG + (UNIT_DMG_BONUS * upgrades.dmg_level)
            stats.attack_cd = max(0.1, UNIT_CD + (UNIT_CD_BONUS * upgrades.cd_level))
            stats.attack_range = 15.0 + (UNIT_RANGE_BONUS * upgrades.range_level)
            
            mov = self.world.component_for_entity(ent, Movement)
            mov.speed = UNIT_SPEED + (UNIT_SPEED_BONUS * upgrades.speed_level)
            
            # Update visual shape based on upgrades
            if upgrades.hp_level > 0 or upgrades.dmg_level > 0 or upgrades.cd_level > 0 or upgrades.speed_level > 0 or upgrades.range_level > 0:
                from shape_generator import generate_unit_shape
                trans = self.world.component_for_entity(ent, Transform)
                rend = self.world.component_for_entity(ent, Renderable)
                
                polygon_points = generate_unit_shape(
                    trans.radius,
                    upgrades.hp_level,
                    upgrades.dmg_level,
                    upgrades.cd_level,
                    upgrades.speed_level,
                    upgrades.range_level
                )
                
                rend.shape = 'polygon'
                rend.polygon_points = polygon_points
            
        elif entity_type == 'castle':
            upgrades.hp_level = self.faction_upgrades[faction_id]['castle_hp']
            upgrades.dmg_level = self.faction_upgrades[faction_id]['castle_dmg']
            upgrades.cd_level = self.faction_upgrades[faction_id]['castle_cd']
            
            stats = self.world.component_for_entity(ent, Stats)
            stats.max_hp = CASTLE_HP + (CASTLE_HP_BONUS * upgrades.hp_level)
            stats.hp = stats.max_hp
            stats.attack_dmg = CASTLE_DMG + (CASTLE_DMG_BONUS * upgrades.dmg_level)
            stats.attack_cd = max(0.1, CASTLE_CD + (CASTLE_CD_BONUS * upgrades.cd_level))
            
        elif entity_type == 'resource':
            upgrades.rate_level = self.faction_upgrades[faction_id]['resource_rate']
            
            if self.world.has_component(ent, ResourceGenerator):
                gen = self.world.component_for_entity(ent, ResourceGenerator)
                gen.rate = RES_GENERATION_RATE + (RESOURCE_RATE_BONUS * upgrades.rate_level)
        
        self.world.add_component(ent, upgrades)

    def create_entity(self, type_name, x, y, faction_id):
        if type_name == 'unit':
            color = self.get_faction_color(faction_id)
            ent = self.world.create_entity(
                Transform(x=x, y=y, radius=UNIT_RADIUS),
                Velocity(),
                Movement(speed=UNIT_SPEED),
                Renderable(color=color, shape='circle', layer=1),
                Identity(faction=faction_id, type='unit'),
                Stats(hp=UNIT_HP, max_hp=UNIT_HP, attack_dmg=UNIT_DMG, attack_range=15.0, attack_cd=UNIT_CD),
            )
            if faction_id == self.player_faction_id:
                self.world.add_component(ent, Selectable())
            # Apply current faction upgrades
            self.apply_faction_upgrades_to_entity(ent, faction_id, 'unit')
            return ent

        elif type_name == 'castle':
            color = self.get_faction_color(faction_id)
            ent = self.world.create_entity(
                Transform(x=x, y=y, radius=CASTLE_RADIUS),
                Renderable(color=color, shape='square', layer=0),
                Identity(faction=faction_id, type='castle'),
                Stats(hp=CASTLE_HP, max_hp=CASTLE_HP, attack_dmg=CASTLE_DMG, attack_range=CASTLE_RANGE, attack_cd=CASTLE_CD),
                ResourceGenerator(rate=RES_GENERATION_RATE) # Castle generates base resources
            )
            self.mark_obstacle(x, y, CASTLE_RADIUS)
            # Apply current faction upgrades
            self.apply_faction_upgrades_to_entity(ent, faction_id, 'castle')
            return ent

        elif type_name == 'resource_point':
            ent = self.world.create_entity(
                Transform(x=x, y=y, radius=RES_POINT_RADIUS),
                Renderable(color=COLOR_RESOURCE, shape='triangle', layer=0),
                Identity(faction=FACTION_NEUTRAL, type='resource'),
                Stats(hp=RES_POINT_HP, max_hp=RES_POINT_HP, attack_dmg=5, attack_range=30.0, attack_cd=1.0), # Hostile neutral
            )
            self.mark_obstacle(x, y, RES_POINT_RADIUS)
            return ent

        elif type_name == 'river':
            ent = self.world.create_entity(
                Transform(x=x, y=y, radius=32),
                Renderable(color=COLOR_RIVER, shape='square', layer=0),
                Identity(faction=FACTION_NEUTRAL, type='obstacle'),
            )
            self.mark_obstacle(x, y, 32)
            return ent

        elif type_name == 'mountain':
            ent = self.world.create_entity(
                Transform(x=x, y=y, radius=32),
                Renderable(color=COLOR_MOUNTAIN, shape='triangle', layer=0),
                Identity(faction=FACTION_NEUTRAL, type='obstacle'),
            )
            self.mark_obstacle(x, y, 32)
            return ent

    def spawn_unit(self, x, y, faction_id=None):
        if faction_id is None:
            faction_id = self.player_faction_id
        if self.resources[faction_id] >= UNIT_COST:
            # Spawn slightly offset
            import random
            off_x = random.uniform(-20, 20)
            off_y = random.uniform(-20, 20)
            self.create_entity('unit', x + off_x, y + off_y, faction_id)
            self.resources[faction_id] -= UNIT_COST
    
    def spawn_projectile(self, from_x, from_y, to_x, to_y, damage, target_ent, color, attacker_faction):
        """Spawn a visual projectile for ranged attacks"""
        ent = self.world.create_entity(
            Transform(x=from_x, y=from_y, radius=3),
            Renderable(color=color, shape='circle', layer=2),  # Layer 2: above units
            Projectile(
                start_x=from_x,
                start_y=from_y,
                target_x=to_x,
                target_y=to_y,
                damage=damage,
                target_entity=target_ent,
                attacker_faction=attacker_faction,
                speed=500.0
            )
        )
        return ent

    def get_path(self, start_x, start_y, end_x, end_y):
        """Calculate pathfinding from start to end, avoiding obstacles."""
        start_cell = (int(start_x // TILE_SIZE), int(start_y // TILE_SIZE))
        end_cell = (int(end_x // TILE_SIZE), int(end_y // TILE_SIZE))
        
        # Bounds check
        if not (0 <= start_cell[0] < self.cols and 0 <= start_cell[1] < self.rows): 
            return [(end_x, end_y)]  # Return direct path if out of bounds
        if not (0 <= end_cell[0] < self.cols and 0 <= end_cell[1] < self.rows): 
            # Clamp end cell to valid bounds
            end_cell = (
                max(0, min(self.cols - 1, end_cell[0])),
                max(0, min(self.rows - 1, end_cell[1]))
            )
        
        # If start or end is on a blocked cell, find nearest walkable cells
        if self.grid[start_cell[1]][start_cell[0]] == 1:
            start_cell = self._find_nearest_walkable(start_cell)
        
        # Allow ending on blocked cells only if it's very close to a walkable cell
        end_is_blocked = self.grid[end_cell[1]][end_cell[0]] == 1
        if end_is_blocked:
            # Try to find a walkable cell near the target
            nearest_walkable = self._find_nearest_walkable(end_cell)
            if nearest_walkable:
                end_cell = nearest_walkable

        # BFS pathfinding
        queue = collections.deque([start_cell])
        came_from = {start_cell: None}
        
        found = False
        while queue:
            current = queue.popleft()
            if current == end_cell:
                found = True
                break
            
            cx, cy = current
            # 8-way movement
            neighbors = [
                (cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1),  # Cardinal
                (cx+1, cy+1), (cx-1, cy-1), (cx+1, cy-1), (cx-1, cy+1)  # Diagonal
            ]
            
            for nx, ny in neighbors:
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    if (nx, ny) not in came_from:
                        # Only move through walkable cells
                        if self.grid[ny][nx] == 0:
                            came_from[(nx, ny)] = current
                            queue.append((nx, ny))
        
        if not found:
            # No path found - return direct path and let collision handle it
            return [(end_x, end_y)]
        
        # Reconstruct path
        path = []
        curr = end_cell
        while curr is not None and curr != start_cell:
            path.append(curr)
            curr = came_from.get(curr)
        path.reverse()
        
        # Convert to world coords (center of tile)
        world_path = []
        for cx, cy in path:
            wx = cx * TILE_SIZE + TILE_SIZE / 2
            wy = cy * TILE_SIZE + TILE_SIZE / 2
            world_path.append((wx, wy))
            
        # Replace last point with exact target for precision
        if world_path:
            world_path[-1] = (end_x, end_y)
        else:
            # If path is empty but we're not at start, add target
            world_path = [(end_x, end_y)]
            
        return world_path
    
    def _find_nearest_walkable(self, cell):
        """Find the nearest walkable cell to the given cell using BFS."""
        cx, cy = cell
        queue = collections.deque([cell])
        visited = {cell}
        
        # Search up to a reasonable distance
        max_search = 10
        iterations = 0
        
        while queue and iterations < max_search * max_search:
            iterations += 1
            current = queue.popleft()
            curr_x, curr_y = current
            
            # Check if this cell is walkable
            if self.grid[curr_y][curr_x] == 0:
                return current
            
            # Expand search
            for dx, dy in [(1,0), (-1,0), (0,1), (0,-1), (1,1), (-1,-1), (1,-1), (-1,1)]:
                nx, ny = curr_x + dx, curr_y + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    neighbor = (nx, ny)
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
        
        # If no walkable cell found, return original
        return cell

    def add_tile(self, tile_type, tile_x, tile_y):
        """
        Add a tile-based entity to the map at the specified tile coordinates.
        
        Args:
            tile_type: Type of tile ('river', 'mountain', 'resource_point')
            tile_x: X coordinate in tile space (0 to cols-1)
            tile_y: Y coordinate in tile space (0 to rows-1)
            
        Returns:
            The created entity ID, or None if out of bounds
        """
        # Validate tile coordinates
        if not (0 <= tile_x < self.cols and 0 <= tile_y < self.rows):
            print(f"Warning: Tile coordinates ({tile_x}, {tile_y}) out of bounds")
            return None
        
        # Convert tile coordinates to world coordinates (center of tile)
        world_x = tile_x * TILE_SIZE + TILE_SIZE / 2
        world_y = tile_y * TILE_SIZE + TILE_SIZE / 2
        
        # Create the appropriate entity type
        if tile_type == 'river':
            ent = self.create_entity('river', world_x, world_y, FACTION_NEUTRAL)
        elif tile_type == 'mountain':
            ent = self.create_entity('mountain', world_x, world_y, FACTION_NEUTRAL)
        elif tile_type == 'resource_point':
            ent = self.create_entity('resource_point', world_x, world_y, FACTION_NEUTRAL)
        else:
            print(f"Warning: Unknown tile type '{tile_type}'")
            return None
        
        return ent

    def generate_terrain(self):
        import random
        # Calculate tile-based center coordinates
        center_tile_x = SCREEN_WIDTH // 2 // TILE_SIZE
        center_tile_y = SCREEN_HEIGHT // 2 // TILE_SIZE
        
        # 1. Rivers: Cross shape dividing map into quadrants, with central bridges
        # Vertical River - goes down the middle horizontally
        for tile_y in range(self.rows):
            # Skip center tiles for bridge (2 tiles gap on each side)
            if abs(tile_y - center_tile_y) < 2:
                continue  # Center Bridge (horizontal)
            self.add_tile('river', center_tile_x, tile_y)

        # Horizontal River - goes across the middle vertically  
        for tile_x in range(self.cols):
            # Skip center tiles for bridge (3 tiles gap on each side for wider bridge)
            if abs(tile_x - center_tile_x) < 3:
                continue  # Center Bridge (vertical)
            self.add_tile('river', tile_x, center_tile_y)

        # 2. Mountains: Strategic clusters to create choke points
        # Define cluster centers in tile coordinates
        # Quadrants: TL, TR, BL, BR
        mountain_clusters = [
            (center_tile_x // 2, center_tile_y // 2),           # Top-Left
            (center_tile_x + center_tile_x // 2, center_tile_y // 2),  # Top-Right
            (center_tile_x // 2, center_tile_y + center_tile_y // 2),  # Bottom-Left
            (center_tile_x + center_tile_x // 2, center_tile_y + center_tile_y // 2)  # Bottom-Right
        ]
        
        for cluster_x, cluster_y in mountain_clusters:
            # Create a small cluster of mountains (3-5 mountains per cluster)
            num_mountains = random.randint(3, 5)
            for _ in range(num_mountains):
                # Offset by a few tiles from cluster center
                offset_x = random.randint(-1, 1)
                offset_y = random.randint(-1, 1)
                tile_x = cluster_x + offset_x
                tile_y = cluster_y + offset_y
                
                # Ensure within bounds
                if 0 <= tile_x < self.cols and 0 <= tile_y < self.rows:
                    self.add_tile('mountain', tile_x, tile_y)

def main():
    pygame.init()
    pygame.display.set_caption("5m War - RTS Prototype")
    window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 18)

    scene = SceneManager()

    # Systems Registration
    from upgrade_system import UpgradeSystem
    from projectile_system import ProjectileSystem
    from cleanup_system import CleanupSystem
    scene.world.add_processor(InputSystem(scene))
    scene.world.add_processor(AISystem(scene))
    scene.world.add_processor(MovementSystem(scene.spatial_hash))
    scene.world.add_processor(CombatSystem(scene.spatial_hash))
    scene.world.add_processor(ProjectileSystem())  # Projectile system for ranged attacks
    scene.world.add_processor(CleanupSystem())  # Process kill requests from combat/projectiles
    scene.world.add_processor(ResourceSystem())
    scene.world.add_processor(ConstructionSystem())
    scene.world.add_processor(WinConditionSystem(scene))
    scene.world.add_processor(UpgradeSystem(scene))  # Add upgrade system
    scene.world.add_processor(RenderSystem(window, font))

    # Initial Setup
    # Create Faction Entities (Color/Name)
    BOT_COLORS = [
        (220, 20, 60),    # Crimson
        (255, 140, 0),    # Orange
        (138, 43, 226),   # Purple
    ]
    
    # Generate Bot Factions
    bot_factions = [str(uuid.uuid4())[:8] for _ in range(3)]
    
    scene.world.create_entity(FactionInfo(id=FACTION_PLAYER, name="PLAYER", color=COLOR_PLAYER))
    scene.world.create_entity(FactionInfo(id=FACTION_NEUTRAL, name="NEUTRAL", color=COLOR_NEUTRAL))
    
    # Initialize faction upgrades for player
    scene.init_faction_upgrades(FACTION_PLAYER)
    
    for i, f in enumerate(bot_factions):
        c = BOT_COLORS[i % len(BOT_COLORS)]
        scene.world.create_entity(FactionInfo(id=f, name=f"AI-{i+1}", color=c))
        
        # Init resources for bots
        scene.resources[f] = STARTING_RESOURCES
        # Init upgrades for bots
        scene.init_faction_upgrades(f)

    # Battle Royale Setup (4 Corners)
    # Player: Top Left
    ent = scene.create_entity('castle', 100, 100, FACTION_PLAYER)
    scene.world.add_component(ent, AIController(auto_spawn=False, auto_attack=False)) # Player controls surplus manually
    
    # Bots placement
    positions = [
        (SCREEN_WIDTH - 100, 100),              # Top Right
        (100, SCREEN_HEIGHT - 100),             # Bottom Left
        (SCREEN_WIDTH - 100, SCREEN_HEIGHT - 100) # Bottom Right
    ]
    
    for i, faction in enumerate(bot_factions):
        if i < len(positions):
            ent = scene.create_entity('castle', positions[i][0], positions[i][1], faction)
            scene.world.add_component(ent, AIController())

    # Generate Terrain
    scene.generate_terrain()

    # Map Resources (placed on strategic tile locations)
    # Center resource
    center_x = SCREEN_WIDTH // 2 // TILE_SIZE
    center_y = SCREEN_HEIGHT // 2 // TILE_SIZE
    scene.add_tile('resource_point', center_x, center_y)
    
    # Top quadrant resources (left and right of center)
    scene.add_tile('resource_point', center_x + 2, 2)
    scene.add_tile('resource_point', center_x - 2, 2)
    
    # Bottom quadrant resources (left and right of center)
    scene.add_tile('resource_point', center_x + 2, scene.rows - 3)
    scene.add_tile('resource_point', center_x - 2, scene.rows - 3)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        scene.dt = dt
        scene.game_time += dt

        # Sudden Death Trigger
        if scene.game_time > SUDDEN_DEATH_TIME and not scene.sudden_death:
            scene.sudden_death = True
            print("SUDDEN DEATH! SPEED UP!")

        # Event Handling
        scene.events = pygame.event.get()
        for event in scene.events:
            if event.type == pygame.QUIT:
                running = False

        # ECS Process
        scene.world.process()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()