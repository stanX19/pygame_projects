"""
True Constraint Satisfaction Problem (CSP) solver with backtracking.
Single unified generation process with forward checking and domain propagation.
"""
import random
import math
from collections import deque
from copy import deepcopy


class TileMapGenerator:
    """
    Unified CSP solver using backtracking search.
    Generates castles, resources, and terrain together in one search process.
    """
    
    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows
        self.grid = [[None for _ in range(cols)] for _ in range(rows)]
        self.domains = None
        
        # CSP state
        self.num_castles_needed = 0
        self.num_resources_needed = 0
        self.castles_placed = []
        self.resources_placed = []
    
    def generate_map(self, num_players=4, max_attempts=1000):
        """Generate map using backtracking CSP with fresh randomization each attempt"""
        self.num_castles_needed = num_players
        self.num_resources_needed = num_players * 2
        
        for attempt in range(max_attempts):
            print(f"Attempt {attempt + 1}...")
            
            # Initialize CSP with fresh state (randomization happens in backtracking)
            self._init_csp()
            
            # Run backtracking search with fresh random candidate ordering
            if self._backtrack_search():
                # Success! Convert and validate
                obstacle_tiles = self._convert_special_tiles()
                obstacle_set = {(ox, oy) for ox, oy, _ in obstacle_tiles}
                
                # Final global constraint checks
                if self._validate_all_global_constraints(obstacle_set):
                    print(f"✓ Valid map generated!")
                    print(f"  Castles: {len(self.castles_placed)}, Resources: {len(self.resources_placed)}, Obstacles: {len(obstacle_tiles)}")
                    return self.castles_placed, self.resources_placed, obstacle_tiles
        
        print(f"✗ CSP failed after {max_attempts} attempts - using fallback")
        return self._generate_fallback(num_players)
    
    def _init_csp(self):
        """Initialize CSP state"""
        self.grid = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        
        # Initial domains: all tiles can be anything
        self.domains = [[{'empty', 'castle', 'resource', 'river_vertical', 'river_horizontal', 'hill_center'} 
                         for _ in range(self.cols)] for _ in range(self.rows)]
        
        self.castles_placed = []
        self.resources_placed = []
    
    def _backtrack_search(self):
        """
        Main backtracking search.
        Returns True if solution found, False if no solution.
        """
        # PHASE 1: Place castles using backtracking
        if not self._place_entities_backtrack('castle', self.num_castles_needed, self.castles_placed):
            return False
        
        # PHASE 2: Place resources using backtracking
        if not self._place_entities_backtrack('resource', self.num_resources_needed, self.resources_placed):
            return False
        
        # PHASE 3: Fill terrain respecting domains
        self._fill_terrain_greedy()
        
        return True
    
    def _place_entities_backtrack(self, entity_type, count_needed, placement_list):
        """
        Backtracking placement for castles or resources.
        Uses forward checking and domain propagation.
        """
        if len(placement_list) == count_needed:
            return True  # All placed successfully
        
        # Get unassigned tiles that can hold this entity type
        candidates = []
        for y in range(self.rows):
            for x in range(self.cols):
                if entity_type in self.domains[y][x] and self.grid[y][x] is None:
                    candidates.append((x, y))
        
        # Shuffle for randomness
        random.shuffle(candidates)
        
        # Try each candidate
        for x, y in candidates:
            # Save state for backtracking
            saved_grid = deepcopy(self.grid)
            saved_domains = deepcopy(self.domains)
            
            # Try assigning this tile
            self.grid[y][x] = entity_type
            placement_list.append((x, y))
            
            # FORWARD CHECK: Propagate constraints
            if self._forward_check(x, y, entity_type):
                # Constraints satisfied, recurse
                if self._place_entities_backtrack(entity_type, count_needed, placement_list):
                    return True  # Success!
            
            # BACKTRACK: Undo assignment
            self.grid = saved_grid
            self.domains = saved_domains
            placement_list.pop()
        
        return False  # No solution found
    
    def _forward_check(self, x, y, entity_type):
        """
        Forward checking: After assigning tile (x,y) to entity_type,
        propagate constraints and check if any domain becomes empty.
        Returns False if constraint violation detected.
        """
        if entity_type == 'castle':
            return self._forward_check_castle(x, y)
        elif entity_type == 'resource':
            return self._forward_check_resource(x, y)
        return True
    
    def _forward_check_castle(self, cx, cy):
        """
        Forward check for castle placement:
        1. Remove obstacle types from 8-neighbor domains
        2. Check castle distance constraints
        3. Check if this creates unsolvable state
        """
        # PROPAGATE: Neighbors cannot be obstacles
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    self.domains[ny][nx].discard('river_vertical')
                    self.domains[ny][nx].discard('river_horizontal')
                    self.domains[ny][nx].discard('hill_center')
                    
                    # Check if domain became empty (unsolvable)
                    if len(self.domains[ny][nx]) == 0:
                        return False
        
        # Check distance from other castles (simple euclidean for now, path checked later)
        for other_cx, other_cy in self.castles_placed[:-1]:  # Exclude current
            if max(abs(cx - other_cx), abs(cy - other_cy)) < 5:  # Minimum euclidean spacing
                return False
        
        return True
    
    def _forward_check_resource(self, rx, ry):
        """
        Forward check for resource placement:
        1. Fix domain to just 'resource'
        2. Check spacing from other resources
        """
        self.domains[ry][rx] = {'resource'}
        
        # Check spacing
        for other_rx, other_ry in self.resources_placed[:-1]:
            if max(abs(rx - other_rx), abs(ry - other_ry)) < 3:
                return False
        
        # Check that each castle so far can potentially reach a resource
        # (Simplified check - just ensure not too far)
        for cx, cy in self.castles_placed:
            has_nearby_resource = False
            for res_x, res_y in self.resources_placed:
                if max(abs(cx - res_x), abs(cy - res_y)) <= 10:
                    has_nearby_resource = True
                    break
            if not has_nearby_resource and len(self.resources_placed) > len(self.castles_placed):
                return False  # No resource near this castle
        
        return True
    
    def _fill_terrain_greedy(self):
        """
        Fill remaining empty tiles with terrain features.
        This is greedy (not backtracking) for performance.
        """
        # Rivers
        for _ in range(random.randint(2, 3)):
            self._grow_river_feature()
        
        # Hills
        for _ in range(random.randint(3, 5)):
            self._grow_hill_feature()
    
    def _grow_river_feature(self):
        """Grow a river respecting domains"""
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        
        if edge == 'top':
            x, y = random.randint(2, self.cols - 3), 0
            dx, dy = 0, 1
            river_type = 'river_vertical'
        elif edge == 'bottom':
            x, y = random.randint(2, self.cols - 3), self.rows - 1
            dx, dy = 0, -1
            river_type = 'river_vertical'
        elif edge == 'left':
            x, y = 0, random.randint(2, self.rows - 3)
            dx, dy = 1, 0
            river_type = 'river_horizontal'
        else:
            x, y = self.cols - 1, random.randint(2, self.rows - 3)
            dx, dy = -1, 0
            river_type = 'river_horizontal'
        
        for step in range(random.randint(8, 15)):
            if not (0 <= x < self.cols and 0 <= y < self.rows):
                break
            
            # Check domain
            if river_type not in self.domains[y][x]:
                x += dx
                y += dy
                continue
            
            # IMPORTANT: Double-check not adjacent to castle
            if self._is_adjacent_to_castle(x, y):
                x += dx
                y += dy
                continue
            
            current = self.grid[y][x]
            
            # Calculate score
            if current == river_type:
                score = 1.0
            elif current is None:
                score = 0.3
            else:
                x += dx
                y += dy
                continue
            
            # Bias: skip empty sometimes
            if score < 0.5 and random.random() < 0.3:
                x += dx
                y += dy
                continue
            
            # Place
            self.grid[y][x] = river_type
            self.domains[y][x] = {river_type}
            
            # Move
            if random.random() < 0.8:
                x += dx
                y += dy
            else:
                if river_type == 'river_vertical':
                    x += random.choice([-1, 1])
                else:
                    y += random.choice([-1, 1])
    
    def _is_adjacent_to_castle(self, x, y):
        """Check if tile (x,y) is adjacent to any castle"""
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    if self.grid[ny][nx] == 'castle':
                        return True
        return False
    
    def _grow_hill_feature(self):
        """Grow a hill cluster respecting domains"""
        for attempt in range(20):
            cx = random.randint(2, self.cols - 3)
            cy = random.randint(2, self.rows - 3)
            
            if ('hill_center' in self.domains[cy][cx] and 
                self.grid[cy][cx] is None and
                not self._is_adjacent_to_castle(cx, cy)):
                break
        else:
            return
        
        cluster = [(cx, cy)]
        to_grow = [(cx, cy)]
        self.grid[cy][cx] = 'hill_center'
        self.domains[cy][cx] = {'hill_center'}
        max_size = random.randint(5, 10)
        
        while to_grow and len(cluster) < max_size:
            x, y = to_grow.pop(0)
            
            neighbors = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
            random.shuffle(neighbors)
            
            for nx, ny in neighbors:
                if not (0 <= nx < self.cols and 0 <= ny < self.rows):
                    continue
                if (nx, ny) in cluster:
                    continue
                if 'hill_center' not in self.domains[ny][nx]:
                    continue
                if self.grid[ny][nx] is not None:
                    continue
                
                # IMPORTANT: Double-check not adjacent to castle
                if self._is_adjacent_to_castle(nx, ny):
                    continue
                
                # Check bias
                has_hill_neighbor = any(
                    0 <= nx+dx < self.cols and 0 <= ny+dy < self.rows and
                    self.grid[ny+dy][nx+dx] == 'hill_center'
                    for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]
                )
                
                dist = max(abs(nx - cx), abs(ny - cy))
                prob = 0.7 / (1 + dist * 0.25)
                if has_hill_neighbor:
                    prob = min(prob * 1.5, 0.95)
                
                if random.random() < prob:
                    cluster.append((nx, ny))
                    to_grow.append((nx, ny))
                    self.grid[ny][nx] = 'hill_center'
                    self.domains[ny][nx] = {'hill_center'}
    
    def _validate_all_global_constraints(self, obstacle_set):
        """Validate all global constraints after generation"""
        # 1. Army traversal distance
        if not self._validate_army_distance(obstacle_set):
            return False
        
        # 2. Connectivity
        if not self._validate_connectivity(obstacle_set):
            return False
        
        # 3. Resource fairness
        if not self._validate_resource_fairness():
            return False
        
        return True
    
    def _validate_army_distance(self, obstacles):
        """Check army traversal distance ≥9 between all castle pairs"""
        for i, castle_a in enumerate(self.castles_placed):
            for castle_b in self.castles_placed[i+1:]:
                dist = self._bfs_distance(castle_a, castle_b, obstacles)
                if dist < 9:
                    return False
        return True
    
    def _bfs_distance(self, start, goal, obstacles):
        """Calculate BFS path distance"""
        queue = deque([(start, 0)])
        visited = {start}
        directions = [(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)]
        
        while queue:
            (x, y), dist = queue.popleft()
            if (x, y) == goal:
                return dist
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.cols and 0 <= ny < self.rows and
                    (nx, ny) not in visited and (nx, ny) not in obstacles):
                    visited.add((nx, ny))
                    queue.append(((nx, ny), dist + 1))
        
        return float('inf')
    
    def _validate_connectivity(self, obstacles):
        """Check all castles connected"""
        if len(self.castles_placed) < 2:
            return True
        
        start = self.castles_placed[0]
        for target in self.castles_placed[1:]:
            if not self._bfs_reachable(start, target, obstacles):
                return False
        return True
    
    def _bfs_reachable(self, start, goal, obstacles):
        """BFS reachability check"""
        queue = deque([start])
        visited = {start}
        directions = [(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)]
        
        while queue:
            x, y = queue.popleft()
            if (x, y) == goal:
                return True
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.cols and 0 <= ny < self.rows and
                    (nx, ny) not in visited and (nx, ny) not in obstacles):
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        
        return False
    
    def _validate_resource_fairness(self):
        """Check each castle has nearest resource"""
        for i, castle in enumerate(self.castles_placed):
            has_nearest = False
            for resource in self.resources_placed:
                dist_to_this = max(abs(castle[0] - resource[0]), abs(castle[1] - resource[1]))
                is_closest = True
                for j, other_castle in enumerate(self.castles_placed):
                    if i == j:
                        continue
                    dist_to_other = max(abs(other_castle[0] - resource[0]), abs(other_castle[1] - resource[1]))
                    if dist_to_other <= dist_to_this:
                        is_closest = False
                        break
                if is_closest:
                    has_nearest = True
                    break
            if not has_nearest:
                return False
        return True
    
    def _convert_special_tiles(self):
        """Convert special tiles to obstacles"""
        obstacles = []
        for y in range(self.rows):
            for x in range(self.cols):
                tile = self.grid[y][x]
                if tile in ['river_vertical', 'river_horizontal']:
                    obstacles.append((x, y, 'river'))
                    self.grid[y][x] = 'river'
                elif tile == 'hill_center':
                    obstacles.append((x, y, 'mountain'))
                    self.grid[y][x] = 'mountain'
        return obstacles
    
    def _generate_fallback(self, num_players):
        """Simple fallback map"""
        self.grid = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        
        castles = [(3, 3), (self.cols-4, self.rows-4), (3, self.rows-4), (self.cols-4, 3)][:num_players]
        for cx, cy in castles:
            self.grid[cy][cx] = 'castle'
        
        resources = []
        for cx, cy in castles:
            for rx, ry in [(cx+6, cy), (cx, cy+6)]:
                if 0 <= rx < self.cols and 0 <= ry < self.rows:
                    resources.append((rx, ry))
                    self.grid[ry][rx] = 'resource'
        
        obstacles = []
        for _ in range(int(self.cols * self.rows * 0.05)):
            tx, ty = random.randint(0, self.cols-1), random.randint(0, self.rows-1)
            if self.grid[ty][tx] is None:
                obstacles.append((tx, ty, 'mountain' if random.random() < 0.67 else 'river'))
        
        return castles, resources, obstacles
