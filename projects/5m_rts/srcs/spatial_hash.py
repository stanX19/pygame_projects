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