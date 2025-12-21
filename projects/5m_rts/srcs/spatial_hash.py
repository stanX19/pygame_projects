"""
Spatial Hashing for optimized proximity queries.
Replaces O(N^2) checks with O(1) average lookup.
"""
import math


class SpatialHash:
    def __init__(self, cell_size):
        self.cell_size = cell_size
        self.grid = {}

    def _get_key(self, x, y):
        return (int(x // self.cell_size), int(y // self.cell_size))

    def clear(self):
        self.grid = {}

    def insert(self, entity_id, x, y, radius=0):
        if radius <= 0:
            # Point insertion
            key = self._get_key(x, y)
            if key not in self.grid:
                self.grid[key] = []
            self.grid[key].append(entity_id)
        else:
            # Area insertion (for large obstacles)
            min_x = int((x - radius) // self.cell_size)
            max_x = int((x + radius) // self.cell_size)
            min_y = int((y - radius) // self.cell_size)
            max_y = int((y + radius) // self.cell_size)
            
            # Avoid inserting duplicate references in the same bucket?
            # Actually we typically insert once per bucket.
            # But we must ensure we don't insert same entity twice in same bucket if radius is small
            # With range loop it handles it correctly.
            
            for cx in range(min_x, max_x + 1):
                for cy in range(min_y, max_y + 1):
                    key = (cx, cy)
                    if key not in self.grid:
                        self.grid[key] = []
                    self.grid[key].append(entity_id)

    def query_nearby(self, x, y):
        """Returns entities in the same cell and 8 neighbors."""
        cx, cy = self._get_key(x, y)
        nearby = []

        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                key = (cx + dx, cy + dy)
                if key in self.grid:
                    nearby.extend(self.grid[key])
        return nearby

    def query_range(self, x, y, radius):
        """Returns entities in all cells that intersect with the given radius."""
        nearby = []
        
        # Calculate grid bounds for the radius
        min_cx = int((x - radius) // self.cell_size)
        max_cx = int((x + radius) // self.cell_size)
        min_cy = int((y - radius) // self.cell_size)
        max_cy = int((y + radius) // self.cell_size)
        
        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                key = (cx, cy)
                if key in self.grid:
                    nearby.extend(self.grid[key])
                    
        return nearby

    def query_first_n(self, x, y, radius, n=1, ignore_entity=None):
        """
        Returns the first n entities in the range of the given radius.
        Optimized for single target entity lookup.
        
        Args:
            x, y: Center position
            radius: Search radius (used to determine grid cell range)
            n: Number of entities to return
            ignore_entity: List of entity IDs to exclude from results
            
        Note: This returns entity IDs from grid cells within range.
        Caller must verify actual distance using Transform components.
        """
        cx, cy = self._get_key(x, y)
        # Use Manhattan distance approximation (radius * 1.414) for better circular coverage
        max_dist = int(radius * 1.414 / self.cell_size) + 1

        entities = []
        # Check center first
        if (cx, cy) in self.grid:
            for entity_id in self.grid[(cx, cy)]:
                if ignore_entity and entity_id in ignore_entity:
                    continue
                entities.append(entity_id)
                if len(entities) >= n:
                    return entities

        # Expanding diamond pattern (Manhattan distance rings)
        for d in range(1, max_dist + 1):
            for dx in range(-d, d + 1):
                dy_abs = d - abs(dx)
                dys = [dy_abs] if dy_abs == 0 else [dy_abs, -dy_abs]
                
                for dy in dys:
                    key = (cx + dx, cy + dy)
                    if key in self.grid:
                        for entity_id in self.grid[key]:
                            if ignore_entity and entity_id in ignore_entity:
                                continue
                            entities.append(entity_id)
                            if len(entities) >= n:
                                return entities
        return entities