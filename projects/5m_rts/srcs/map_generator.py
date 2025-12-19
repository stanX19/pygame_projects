"""
True Constraint Satisfaction Problem (CSP) solver with backtracking.
Single unified generation process with forward checking and domain propagation.
"""
import random
import math
from collections import deque
from copy import deepcopy


import config

class TileMapGenerator:
    """
    Unified CSP solver using backtracking search.
    Generates castles, resources, and terrain together in one search process.
    """
    
    def __init__(self, cols, rows, visualize_callback=None, delay=0.0):
        self.cols = cols
        self.rows = rows
        self.grid = [[None for _ in range(cols)] for _ in range(rows)]
        self.domains = None
        
        # CSP state
        self.num_castles_needed = 0
        self.num_resources_needed = 0 # Will be calculated dynamically
        self.total_resources_needed = 0
        self.castles_placed = []
        self.resources_placed = []
        
        # Visualization
        self.visualize_callback = visualize_callback
        self.delay = delay  # Delay in seconds between visualization updates
        
        # Debug tracking
        self._last_constraint_failure = ""
    
    def generate_map(self, num_players=4, max_attempts=1000):
        """Generate map using backtracking CSP with fresh randomization each attempt"""
        self.num_castles_needed = num_players
        # Total resources = guaranteed per castle + extra scattered ones
        self.total_resources_needed = (num_players * config.RESOURCES_PER_CASTLE) + config.EXTRA_RESOURCES
        
        for attempt in range(max_attempts):
            print(f"Attempt {attempt + 1}...")
            
            # Initialize CSP with fresh state (randomization happens in backtracking)
            self._init_csp()
            
            # Run backtracking search with fresh random candidate ordering
            if self._backtrack_search():
                print("DEBUG: Backtrack search SUCCEEDED!")
                # Success! Convert and return
                obstacle_tiles = self._convert_special_tiles()
                
                print(f"✓ Valid map generated!")
                print(f"  Castles: {len(self.castles_placed)}, Resources: {len(self.resources_placed)}, Obstacles: {len(obstacle_tiles)}")
                return self.castles_placed, self.resources_placed, obstacle_tiles
        
        print(f"✗ CSP failed after {max_attempts} attempts - using fallback")
        return self._generate_fallback(num_players)
    
    def _init_csp(self):
        """Initialize CSP state"""
        self.grid = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        
        # Initial domains: all tiles can be anything
        # river_vertical/horizontal create continuous river lines
        # hill/hill_center create mountain clusters
        self.domains = [[{'empty', 'castle', 'resource', 'river_vertical', 'river_horizontal', 'river', 'hill_center', 'hill', 'fieldland'} 
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
        
        # Remove 'castle' from all domains after castle placement phase
        for y in range(self.rows):
            for x in range(self.cols):
                if 'castle' in self.domains[y][x]:
                    self.domains[y][x].discard('castle')
        
        # PHASE 2: Place Guaranteed Resources & Carve Paths (NEW)
        # This ensures each castle has fairness before we fill the rest
        if not self._place_guaranteed_resources():
            return False
            
        # PHASE 3: Unified resource + terrain placement with backtracking
        if not self._place_resources_and_terrain_backtrack():
            return False
        
        return True

    def _place_guaranteed_resources(self):
        """
        Place guaranteed resources near each castle and carve paths to them.
        This modifies self.grid and self.domains directly.
        Returns True if successful, False if cannot place.
        """
        print("DEBUG: Placing guaranteed resources...")
        
        for cx, cy in self.castles_placed:
            placed_count = 0
            attempts = 0
            
            while placed_count < config.RESOURCES_PER_CASTLE and attempts < 50:
                attempts += 1
                
                # Pick a spot near the castle (radius 2-4)
                # Spiral out or random selection in range
                rx = cx + random.randint(-4, 4)
                ry = cy + random.randint(-4, 4)
                
                # Check bounds
                if not (0 <= rx < self.cols and 0 <= ry < self.rows):
                    continue
                    
                # Calculate distance
                dist = abs(rx - cx) + abs(ry - cy) # Manhattan
                if dist < 2 or dist > 5: # Don't place too close (adjacency) or too far
                    continue
                
                # Check if spot is free
                if self.grid[ry][rx] is not None:
                    continue
                    
                # Check spacing from other resources (even guaranteed ones)
                too_close = False
                for ox, oy in self.resources_placed:
                    if max(abs(rx - ox), abs(ry - oy)) < 2: # Min 2 tiles between any resources
                        too_close = True
                        break
                if too_close:
                    continue
                
                # Check not adjacent to ANY castle (including this one's 8-neighbors)
                if self._is_adjacent_to_castle(rx, ry):
                    continue
                
                # PLACE IT
                self.grid[ry][rx] = 'resource'
                self.domains[ry][rx] = {'resource'}
                self.resources_placed.append((rx, ry))
                placed_count += 1
                
                # CARVE PATH: Make line from castle to resource 'empty'
                self._carve_path_to_resource(cx, cy, rx, ry)
                
            if placed_count < config.RESOURCES_PER_CASTLE:
                print(f"Failed to place guaranteed resources for castle at {cx},{cy}")
                return False
                
        return True
    
    def _carve_path_to_resource(self, cx, cy, rx, ry):
        """Force a path of empty tiles between castle and resource."""
        # Simple L-shape or diagonal walk
        curr_x, curr_y = cx, cy
        
        # Use a simple while loop to move towards target
        step_limit = 20
        while (curr_x != rx or curr_y != ry) and step_limit > 0:
            step_limit -= 1
            
            # Move towards target
            if curr_x < rx: dx = 1
            elif curr_x > rx: dx = -1
            else: dx = 0
            
            if curr_y < ry: dy = 1
            elif curr_y > ry: dy = -1
            else: dy = 0
            
            # Prefer moving in one axis at a time to look nicer (L-shape)
            # but allow diagonals if stuck
            if dx != 0 and dy != 0:
                if random.random() < 0.5: dy = 0
                else: dx = 0
                
            curr_x += dx
            curr_y += dy
            
            # Don't overwrite the resource itself
            if curr_x == rx and curr_y == ry:
                break
                
            # Don't overwrite castle (shouldn't happen as we start from it)
            if (curr_x, curr_y) == (cx, cy):
                continue
                
            # If spot is free, make it empty
            if self.grid[curr_y][curr_x] is None:
                self.grid[curr_y][curr_x] = 'empty'
                self.domains[curr_y][curr_x] = {'empty'}
            # If it's already a resource or castle, we might have an issue, but we skip

    
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
        1. Force 8-neighbors to be empty only (no terrain, no resources)
        2. Check castle distance constraints
        3. Check if this creates unsolvable state
        """
        # PROPAGATE: All 8 neighbors must be empty only
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue  # Skip the castle tile itself
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    # Force this neighbor to be empty only
                    self.domains[ny][nx] = {'empty'}
        
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
        3. Check that each castle has at least one resource within 3 tiles
        """
        self.domains[ry][rx] = {'resource'}
        
        # Check spacing
        for other_rx, other_ry in self.resources_placed[:-1]:
            if max(abs(rx - other_rx), abs(ry - other_ry)) < 3:
                return False
        
        # After placing enough resources, verify each castle has one within 3 tiles
        # Only check this constraint once we've placed at least as many resources as castles
        if len(self.resources_placed) >= len(self.castles_placed):
            for cx, cy in self.castles_placed:
                has_close_resource = False
                for res_x, res_y in self.resources_placed:
                    # Calculate Manhattan distance (path-based distance)
                    manhattan_dist = abs(cx - res_x) + abs(cy - res_y)
                    if manhattan_dist <= 3:
                        has_close_resource = True
                        break
                if not has_close_resource:
                    return False  # This castle has no resource within 3 tiles
        
        return True
    
    def _place_resources_and_terrain_backtrack(self):
        """
        Unified CSP backtracking for ALL tiles (resources + terrain).
        Assigns values to tiles one by one, backtracking on constraint violations.
        """
        # Count resources already placed (guaranteed ones)
        # We start backtracking from 0, but _assign_tiles_backtrack needs to know we have some pre-filled grid
        result = self._assign_tiles_backtrack(0)
        if not result:
            print("DEBUG: ===== ENTIRE CSP ATTEMPT FAILED - RESTARTING =====")
        return result
    
    def _get_next_unassigned_tile_bfs(self):
        """
        Find the next unassigned tile using BFS from all castle locations.
        Returns (x, y) tuple of next tile to assign, or None if all assigned.
        """
        if not self.castles_placed:
            # No castles yet, fall back to top-left to bottom-right
            for y in range(self.rows):
                for x in range(self.cols):
                    if self.grid[y][x] is None:
                        return (x, y)
            return None
        
        # BFS from all castles simultaneously
        queue = deque()
        visited = set()
        
        # Initialize queue with all castle positions
        for castle_x, castle_y in self.castles_placed:
            queue.append((castle_x, castle_y))
            visited.add((castle_x, castle_y))

        # add four corners
        queue.append((0, 0))
        queue.append((self.cols - 1, 0))
        queue.append((0, self.rows - 1))
        queue.append((self.cols - 1, self.rows - 1))
        
        # 4-directional movement (cardinal directions)
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        while queue:
            x, y = queue.popleft()
            
            # Check all neighbors
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                
                # Skip if out of bounds or already visited
                if not (0 <= nx < self.cols and 0 <= ny < self.rows):
                    continue
                if (nx, ny) in visited:
                    continue
                
                visited.add((nx, ny))
                
                # If this tile is unassigned, return it
                if self.grid[ny][nx] is None:
                    return (nx, ny)
                
                # Otherwise, add to queue to continue BFS
                queue.append((nx, ny))
        
        # All tiles visited and assigned
        return None

    
    def _assign_tiles_backtrack(self, num_assigned):
        """
        Backtracking assignment for all tiles.
        When resource cap reached, removes 'resource' from domains.
        Continues assigning terrain until map is complete or constraints fail.
        Uses BFS-like propagation from castle locations.
        """
        # Find next unassigned tile using BFS from castles
        next_tile = self._get_next_unassigned_tile_bfs()
        if next_tile is None:
            # All tiles assigned successfully
            return True
        
        x, y = next_tile
        # Try assigning values from domain
        domain_copy = list(self.domains[y][x])
        
        # If resource cap reached, remove 'resource' from possibilities
        if len(self.resources_placed) >= self.total_resources_needed and 'resource' in domain_copy:
            domain_copy.remove('resource')
        
        # Apply probability weights
        # - 'empty' gets very low weight (but still selectable as fallback)
        # - 'river' and 'hill' get lower weight to reduce over-representation
        # - Other types get normal weight
        weighted_values = []
        for value in domain_copy:
            if value == 'empty':
                weight = 0.1  # Very low, but still possible
            elif value == 'fieldland':
                weight = 1.0
            elif value in ['river', 'hill']:
                weight = 0.3
            else:
                weight = 1.0
            weighted_values.extend([value] * int(weight * 10))
        
        # Shuffle weighted list for randomness
        random.shuffle(weighted_values)
        
        # Try each value (with duplicates for weighting)
        tried_values = set()
        for value in weighted_values:
            if value in tried_values:
                continue  # Skip duplicates
            tried_values.add(value)
            # Save state for backtracking
            saved_grid = deepcopy(self.grid)
            saved_domains = deepcopy(self.domains)
            saved_resources_len = len(self.resources_placed)
            
            # Assign value
            self.grid[y][x] = value
            
            # Track resource placements
            if value == 'resource':
                self.resources_placed.append((x, y))
            
            # Visualize current state
            if self.visualize_callback:
                self.visualize_callback(self.grid, self.domains)
                if self.delay > 0:
                    import time
                    time.sleep(self.delay)
            
            # Check constraints
            constraint_failed = False
            failure_reason = ""
            
            if not self._check_tile_constraints(x, y, value):
                constraint_failed = True
                failure_reason = self._last_constraint_failure
            
            if not constraint_failed:
                # Recurse
                if self._assign_tiles_backtrack(num_assigned + 1):
                    return True  # Success!
                else:
                    failure_reason = "recursive backtrack failed"
            
            # BACKTRACK
            neighbors_info = []
            for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    neighbors_info.append(f"{self.grid[ny][nx] or 'None'}")
                else:
                    neighbors_info.append("OOB")
            neighbors_str = f"[{','.join(neighbors_info)}]"
            print(f"  DEBUG: Backtrack at ({x},{y}) value={value} neighbors={neighbors_str}: {failure_reason}")
            
            self.grid = saved_grid
            self.domains = saved_domains
            # Restore resource list to saved length (recursion may have added multiple)
            while len(self.resources_placed) > saved_resources_len:
                self.resources_placed.pop()
        
        # No valid value for this tile
        return False
    
    def _check_tile_constraints(self, x, y, value):
        """
        Check all constraints for assigning value to tile (x, y).
        Returns False if constraint violated.
        """
        self._last_constraint_failure = ""
        
        # Resource-specific constraints
        if value == 'resource':
            for rx, ry in self.resources_placed[:-1]:
                # Check distance to other resources
                if max(abs(x - rx), abs(y - ry)) < 3: # Keep minimum 3 for any resource pair
                     self._last_constraint_failure = "resource too close to another"
                     return False
            
            # CRITICAL: Extra resources must be far from ANY castle
            # (Guaranteed resources are close, but they are already placed and won't trigger this check 
            #  because we only check constraints for the 'value' we are acting on, and we skip pre-assigned tiles)
            for cx, cy in self.castles_placed:
                dist = abs(x - cx) + abs(y - cy)
                if dist < config.MIN_RESOURCE_DIST:
                    self._last_constraint_failure = "via extra resource: too close to castle"
                    return False
            
            # Check pathfinding: resource must be reachable from all castles
            if not self._check_resource_accessible_from_castles(x, y):
                self._last_constraint_failure = "resource not accessible from castles"
                return False
        
        
        # Terrain continuity constraints - propagate to create organized features
        if value in ['river_vertical', 'river_horizontal', 'hill_center', 'fieldland']:
            # DEBUG: Log what neighbors look like before propagation
            if value in ['river_vertical', 'river_horizontal', 'hill_center']:
                assigned_neighbors = []
                for nx, ny in [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]:
                    if 0 <= nx < self.cols and 0 <= ny < self.rows:
                        if self.grid[ny][nx] is not None:
                            assigned_neighbors.append(f"{self.grid[ny][nx]}")
                if len(assigned_neighbors) >= 2 and 'empty' in assigned_neighbors:
                    print(f"  DEBUG: Placing {value} at ({x},{y}) with assigned neighbors: {assigned_neighbors}")
            self._propagate_terrain_constraints(x, y, value)
        
        # Castle adjacency check (no terrain near castles)
        if value in ['river_vertical', 'river_horizontal', 'river', 'hill_center', 'hill', 'fieldland']:
            if self._is_adjacent_to_castle(x, y):
                self._last_constraint_failure = "adjacent to castle"
                return False

        if not self._check_global_connectivity():
            if not self._last_constraint_failure:
                self._last_constraint_failure = "global connectivity failed"
            return False
        
        return True
    
    def _check_global_connectivity(self):
        """
        Flood fill validation to ensure:
        1. All castles can reach each other
        2. All castles can reach all resources
        
        Note: We don't check empty tiles - they're just decorative and don't need to be accessible.
        Only gameplay-critical elements (castles, resources) must be mutually reachable.
        """
        if len(self.castles_placed) == 0:
            return True
        
        obstacles = self._get_current_obstacles()
        
        # Start flood fill from first castle
        start = self.castles_placed[0]
        reachable = self._flood_fill(start, obstacles)
        
        # Check all castles are reachable
        for castle in self.castles_placed[1:]:
            if castle not in reachable:
                return False
        
        # Check all resources are reachable
        for resource in self.resources_placed:
            if resource not in reachable:
                return False
    
        # 1. Army traversal distance
        if not self._validate_army_distance(obstacles):
            return False
        
        # 2. Connectivity
        if not self._validate_connectivity(obstacles):
            return False
        
        # 3. 2-Path Connectivity Rule
        if not self._check_min_2_paths(obstacles):
            self._last_constraint_failure = "castle <2 disjoint paths"
            return False
            
        # 4. Castle Distance Uniformity (Anomaly Detection)
        if not self._validate_castle_distance_uniformity(obstacles):
             return False

        # 5. Resource fairness
        if not self._validate_resource_fairness():
            return False
        
        return True
    
    def _flood_fill(self, start, obstacles):
        """
        Flood fill from start position, returning set of all reachable tiles.
        Uses 4-directional movement (cardinal directions only).
        """
        from collections import deque
        
        reachable = set()
        queue = deque([start])
        reachable.add(start)
        
        # 4-directional movement only (up, down, left, right)
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        while queue:
            x, y = queue.popleft()
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                
                if not (0 <= nx < self.cols and 0 <= ny < self.rows):
                    continue
                if (nx, ny) in reachable:
                    continue
                if (nx, ny) in obstacles:
                    continue
                
                # Check if tile is walkable
                tile = self.grid[ny][nx]
                if tile is None:
                    # Unassigned - check if 'empty' is in domain
                    if 'empty' not in self.domains[ny][nx]:
                        continue
                elif tile not in ['empty', 'castle', 'resource', 'fieldland']:
                    # Assigned obstacle
                    continue
                
                reachable.add((nx, ny))
                queue.append((nx, ny))
        
        return reachable
    
    def _propagate_adjacency_constraint(self, x, y, requires_empty):
        """
        Propagate adjacency constraint to neighbors.
        If no neighbors are empty yet, force one unassigned neighbor to be empty.
        """
        neighbors = []
        unassigned_neighbors = []
        
        # Determine which directions to check based on tile type
        # Empty tiles check 4-directional, resources check 8-directional
        if self.grid[y][x] == 'empty':
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Cardinal only
        else:
            directions = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if not (dx == 0 and dy == 0)]  # All 8
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.cols and 0 <= ny < self.rows:
                neighbors.append((nx, ny))
                if self.grid[ny][nx] is None:
                    unassigned_neighbors.append((nx, ny))
        
        # Count how many neighbors are already empty/castle
        empty_count = 0
        for nx, ny in neighbors:
            tile = self.grid[ny][nx]
            if tile == 'empty' or tile == 'castle':
                empty_count += 1
        
        # If no neighbors are empty yet and we have unassigned neighbors,
        # FORCE one unassigned neighbor to be empty
        if empty_count == 0 and unassigned_neighbors:
            # Pick first unassigned neighbor and force it to be empty only
            nx, ny = unassigned_neighbors[0]
            if 'empty' in self.domains[ny][nx]:
                # Force this neighbor to be empty only
                self.domains[ny][nx] = {'empty'}
            else:
                # Can't satisfy constraint - fail
                return False
    
    def _has_adjacent_empty(self, x, y):
        """Check if tile has at least one adjacent empty tile (8-directional)."""
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    if self.grid[ny][nx] == 'empty' or self.grid[ny][nx] is None and 'empty' in self.domains[ny][nx]:
                        return True
        return False
    
    def _has_adjacent_empty_or_castle(self, x, y):
        """Check if tile has at least one adjacent empty or castle tile (4-directional: up/down/left/right)."""
        # Only check cardinal directions (no diagonals)
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.cols and 0 <= ny < self.rows:
                tile = self.grid[ny][nx]
                if tile == 'empty' or tile == 'castle':
                    return True
                # Check unassigned tiles that could be empty
                if tile is None and 'empty' in self.domains[ny][nx]:
                    return True
        return False
    
    def _propagate_terrain_constraints(self, x, y, value):
        """
        Propagate terrain continuity constraints to neighbor domains.
        This creates organized terrain features instead of random single tiles.
        """
        if value == 'river_vertical':
            # Up/down neighbors should continue the river vertically
            for ny in [y - 1, y + 1]:
                if 0 <= ny < self.rows and self.grid[ny][x] is None:
                    allowed = {'river_vertical', 'river', 'empty'}
                    self.domains[ny][x] &= allowed
                    
        elif value == 'river_horizontal':
            # Left/right neighbors should continue the river horizontally
            for nx in [x - 1, x + 1]:
                if 0 <= nx < self.cols and self.grid[y][nx] is None:
                    allowed = {'river_horizontal', 'river', 'empty'}
                    self.domains[y][nx] &= allowed
                    
        elif value == 'hill_center':
            # Cardinal neighbors should be hills to form a cluster
            for nx, ny in [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]:
                if 0 <= nx < self.cols and 0 <= ny < self.rows and self.grid[ny][nx] is None:
                    allowed = {'hill_center', 'hill', 'empty'}
                    self.domains[ny][nx] &= allowed
        
        elif value == 'fieldland':
            # Cardinal neighbors must be empty (fieldland requires all 4 directions to be empty)
            for nx, ny in [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]:
                if 0 <= nx < self.cols and 0 <= ny < self.rows and self.grid[ny][nx] is None:
                    allowed = {'empty'}
                    self.domains[ny][nx] &= allowed
        # Generic 'river' doesn't propagate - it's for isolated river tiles or endpoints
    
    def _check_resource_accessible_from_castles(self, rx, ry):
        """
        Check if the resource at (rx, ry) is accessible from all castles.
        Uses BFS to verify path exists considering current obstacles.
        Treats unassigned tiles with 'empty' in domain as potentially walkable.
        """
        obstacles = self._get_current_obstacles()
        
        # Check accessibility from each castle
        for cx, cy in self.castles_placed:
            if not self._bfs_reachable((cx, cy), (rx, ry), obstacles):
                return False
        
        return True
    
    def _bfs_reachable(self, start, goal, obstacles):
        """
        BFS to check if goal is reachable from start.
        Treats unassigned tiles with 'empty' in domain as walkable.
        Uses 4-directional movement (cardinal directions only).
        """
        from collections import deque
        
        if start == goal:
            return True
        
        queue = deque([start])
        visited = {start}
        
        # 4-directional movement only (up, down, left, right)
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        while queue:
            x, y = queue.popleft()
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                
                if not (0 <= nx < self.cols and 0 <= ny < self.rows):
                    continue
                if (nx, ny) in visited:
                    continue
                if (nx, ny) in obstacles:
                    continue
                
                # Check if tile is walkable
                tile = self.grid[ny][nx]
                if tile is None:
                    # Unassigned - check if 'empty' is in domain (potentially walkable)
                    if 'empty' not in self.domains[ny][nx]:
                        continue
                elif tile not in ['empty', 'castle', 'resource', 'fieldland']:
                    # Assigned obstacle
                    continue
                
                visited.add((nx, ny))
                
                if (nx, ny) == goal:
                    return True
                
                queue.append((nx, ny))
        
        return False
    
    def _get_current_obstacles(self):
        """Get set of current obstacle positions (fieldland is NOT an obstacle, it's passable)."""
        obstacles = set()
        for y in range(self.rows):
            for x in range(self.cols):
                tile = self.grid[y][x]
                if tile in ['river_vertical', 'river_horizontal', 'river', 'hill_center', 'hill']:
                    obstacles.add((x, y))
        return obstacles
    
    def _check_min_2_paths(self, obstacles):
        """
        Ensure each castle has at least 2 disjoint paths to the network of other castles.
        Rule: Starting from 4 adjacent tiles, at least 2 must be able to reach another castle's adjacent tile without intersecting.
        """
        if len(self.castles_placed) < 2:
            return True # Trivial

        # Pre-calculate all valid neighbor tiles for each castle
        # Valid neighbor = traversable tile (not in obstacles)
        castle_neighbors = {}
        for cx, cy in self.castles_placed:
            nbs = []
            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                nx, ny = cx + dx, cy + dy
                # Check bounds
                if not (0 <= nx < self.cols and 0 <= ny < self.rows):
                    continue
                # Check obstacles (note: neighbors cannot be obstacles)
                if (nx, ny) in obstacles:
                    continue
                # Note: unassigned tiles (None) are traversable if they simplify to empty
                # Assigned tiles must be traversable (empty, castle, resource, fieldland)
                # But castles are usually obstacles for pathfinding THROUGH them...
                # However, the rule says "from 4 adjacent tile... reach another castle's adjacent tile".
                # It doesn't imply going through the castle.
                # Just checks if path exists.
                
                # We need to check if tile is walkable like in _flood_fill
                tile = self.grid[ny][nx]
                if tile is None:
                    if 'empty' not in self.domains[ny][nx]:
                       continue
                elif tile not in ['empty', 'castle', 'resource', 'fieldland']:
                    continue
                
                nbs.append((nx, ny))
            castle_neighbors[(cx, cy)] = nbs

        for start_castle in self.castles_placed:
            # Sources = neighbors of start_castle
            sources = castle_neighbors.get(start_castle, [])
            if len(sources) < 2:
                # Less than 2 traversable exits -> fail immediately
                return False

            # Targets = neighbors of all OTHER castles
            targets = set()
            for other_c in self.castles_placed:
                if other_c == start_castle: continue
                # We union all neighbors of other castles
                for nb in castle_neighbors.get(other_c, []):
                    targets.add(nb)
            
            if not targets:
                 continue # Maybe other castles have no exits? Then they will fail their check.

            # Try to find 2 disjoint paths from 'sources' to 'targets'
            # Path 1
            path1 = self._bfs_find_path_set_to_set(sources, targets, obstacles, blocked=set())
            if not path1:
                 return False

            # Path 2 (cannot use nodes from path1, except potentially targets if we treat them broad, but strictly disjoint means node disjoint)
            # The rule "without intersecting each other" implies node disjointness.
            blocked_for_p2 = set(path1)
            
            # Note: sources and targets are sets. 
            # If path1 starts at S1 and ends at T1...
            # path2 must start at S2 (S2 != S1? Not necessarily, but S1 is in blocked_for_p2, so S2!=S1 is enforced)
            # path2 end at T2 (T2 != T1? T1 is in blocked_for_p2, so T2!=T1 is enforced)
            # This is strictly node-disjoint including endpoints.
            # Usually for "2 paths from A to B", start/end are shared.
            # But here we are going from Set S to Set T.
            # "At least 2 must be able to reach... without intersecting".
            # This implies the paths starting from different neighbors.
            # So start nodes MUST be different. blocked_for_p2 ensures that.
            
            path2 = self._bfs_find_path_set_to_set(sources, targets, obstacles, blocked=blocked_for_p2)
            if not path2:
                return False
                
        return True

    def _bfs_find_path_set_to_set(self, start_nodes, target_nodes, obstacles, blocked):
        """
        Find shortest path from any start_node to any target_node.
        Returns list of nodes in path (inclusive), or None.
        blocked: set of nodes to avoid
        """
        # Filter starts that are blocked
        valid_starts = [n for n in start_nodes if n not in blocked]
        if not valid_starts:
            return None

        # Standard BFS
        queue = deque()
        visited = set(blocked) # Treat blocked as visited
        parent_map = {} # to reconstruct path
        
        for s in valid_starts:
            queue.append(s)
            visited.add(s)
            parent_map[s] = None
        
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        while queue:
            curr = queue.popleft()
            
            if curr in target_nodes:
                # Found path! Reconstruct
                path = []
                node = curr
                while node is not None:
                    path.append(node)
                    node = parent_map[node]
                return path[::-1] # Reverse to start->end
            
            cx, cy = curr
            for dx, dy in directions:
                nx, ny = cx + dx, cy + dy
                
                if not (0 <= nx < self.cols and 0 <= ny < self.rows):
                    continue
                if (nx, ny) in visited:
                    continue
                if (nx, ny) in obstacles:
                    continue
                
                # Check walkable (same logic as usual)
                # But here we assume obstacles set covers hard obstacles.
                # What about unassigned domains?
                # We need to check grid/domain again or trust obstacles set + logic?
                # _check_min_2_paths passed `obstacles` which comes from _get_current_obstacles
                # _get_current_obstacles has 'hill', 'river'.
                # But it doesn't check 'empty' domain for None tiles.
                # So we must verify walkability.
                
                tile = self.grid[ny][nx]
                if tile is None:
                    if 'empty' not in self.domains[ny][nx]:
                        visited.add((nx, ny))
                        continue
                elif tile not in ['empty', 'castle', 'resource', 'fieldland']:
                     visited.add((nx, ny))
                     continue
                
                visited.add((nx, ny))
                parent_map[(nx, ny)] = curr
                queue.append((nx, ny))
                
        return None
    
    def _check_resource_accessible_from_castles(self, rx, ry):
        """
        Check if the resource at (rx, ry) is accessible from all castles.
        Uses BFS to verify path exists considering current obstacles.
        """
        obstacles = self._get_current_obstacles()
        
        # Check accessibility from each castle
        for cx, cy in self.castles_placed:
            if not self._bfs_reachable((cx, cy), (rx, ry), obstacles):
                return False
        
        return True
    
    def _check_no_isolated_tiles(self, obstacles):
        """
        Check that all walkable tiles form a single connected component.
        Returns False if there are isolated empty tile regions.
        """
        # Find all walkable tiles
        walkable = set()
        for y in range(self.rows):
            for x in range(self.cols):
                if (x, y) not in obstacles:
                    walkable.add((x, y))
        
        if not walkable:
            return True  # No walkable tiles to check
        
        # BFS from first walkable tile to find connected component
        start = next(iter(walkable))
        visited = set()
        queue = deque([start])
        visited.add(start)
        
        directions = [(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)]
        
        while queue:
            x, y = queue.popleft()
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.cols and 0 <= ny < self.rows and
                    (nx, ny) not in visited and (nx, ny) in walkable):
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        
        # All walkable tiles should be visited (single connected component)
        return len(visited) == len(walkable)
    
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
            
            # Apply terrain continuity constraint: river_vertical neighbors (up/down) should be river_vertical or generic river
            if river_type == 'river_vertical':
                # Propagate to up and down neighbors
                for ny in [y - 1, y + 1]:
                    if 0 <= ny < self.rows and self.grid[ny][x] is None:
                        # Remove non-river types from domain, keep only river_vertical and river
                        self.domains[ny][x] &= {'river_vertical', 'river', 'empty'}
            elif river_type == 'river_horizontal':
                # Propagate to left and right neighbors  
                for nx in [x - 1, x + 1]:
                    if 0 <= nx < self.cols and self.grid[y][nx] is None:
                        # Remove non-river types from domain, keep only river_horizontal and river
                        self.domains[y][nx] &= {'river_horizontal', 'river', 'empty'}
            
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
        
        # Apply terrain continuity constraint for initial hill center
        for nnx, nny in [(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)]:
            if 0 <= nnx < self.cols and 0 <= nny < self.rows and self.grid[nny][nnx] is None:
                self.domains[nny][nnx] &= {'hill_center', 'hill', 'empty'}
        
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
                    
                    # Apply terrain continuity constraint: hill_center neighbors (cardinal) should be hill_center or hill
                    for nnx, nny in [(nx+1, ny), (nx-1, ny), (nx, ny+1), (nx, ny-1)]:
                        if 0 <= nnx < self.cols and 0 <= nny < self.rows and self.grid[nny][nnx] is None:
                            # Remove non-hill types from domain, keep only hill_center and hill
                            self.domains[nny][nnx] &= {'hill_center', 'hill', 'empty'}
    

    def _validate_castle_distance_uniformity(self, obstacles):
        """
        Check if castle distances are uniform (no anomalies).
        Calculates the nearest neighbor distance for each castle.
        Rejects if Standard Deviation of these distances > Threshold.
        """
        if len(self.castles_placed) < 3:
            return True # Not enough data for meaningful std dev
            
        min_distances = []
        max_distances = []
        total_distances = []
        all_distances = []
        threat_levels = []
        for i, c1 in enumerate(self.castles_placed):
            distances = []
            for j, c2 in enumerate(self.castles_placed):
                if i == j: continue
                
                # Get path distance
                dist = self._bfs_distance(c1, c2, obstacles)
                distances.append(dist)
            
            min_distances.append(min(distances))
            max_distances.append(max(distances))
            total_distances.append(sum(distances))
            all_distances.extend(distances)
            threat_levels.append(sum(1/d for d in distances))
        
        # values = threat_levels
        # thres = 0.05 #config.CASTLE_DIST_DIFF_THRESHOLD #* len(self.castles_placed)
        values = min_distances
        thres = config.CASTLE_DIST_DIFF_THRESHOLD
        mean = sum(values) / len(values)
        std_dev = (sum((x - mean) ** 2 for x in values) / len(values)) ** 0.5
        diff = max(values) - min(values)
        print([f"{x:.2f}" for x in threat_levels], diff, thres)
        if diff > thres:
            self._last_constraint_failure = f"castle dist anomaly (std_dev={std_dev} > 1)"
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
        directions = [(0,1), (1,0), (0,-1), (-1,0)]#, (1,1), (-1,-1), (1,-1), (-1,1)]
        
        while queue:
            (x, y), dist = queue.popleft()
            if (x, y) == goal:
                return dist
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                additional_dist = 2 if (dx, dy) in [(1,1), (-1,-1), (1,-1), (-1,1)] else 1
                if (0 <= nx < self.cols and 0 <= ny < self.rows and
                    (nx, ny) not in visited and (nx, ny) not in obstacles):
                    visited.add((nx, ny))
                    queue.append(((nx, ny), dist + additional_dist))
        
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
                if tile in ['river_vertical', 'river_horizontal', 'river']:
                    obstacles.append((x, y, 'river'))
                    self.grid[y][x] = 'river'
                elif tile in ['hill_center', 'hill']:
                    obstacles.append((x, y, 'mountain'))
                    self.grid[y][x] = 'mountain'
                elif tile == 'fieldland':
                    pass  # Fieldland is decorative, not an obstacle
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
