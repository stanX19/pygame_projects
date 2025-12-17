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

    def insert(self, entity_id, x, y):
        key = self._get_key(x, y)
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