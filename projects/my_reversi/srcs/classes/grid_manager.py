import math
import random
from typing import Union, Callable

from .unit import Unit, Black, White


class GridRow:
    def __init__(self, grid, y: int):
        self.grid = grid
        self.y = y
        self.y += self.grid.grid_size * (self.y < 0)

    def __getitem__(self, col):
        return self.grid.grid[self.y][col]

    def __setitem__(self, x: int, value: Union[None, Unit]):
        x += self.grid.grid_size * (x < 0)
        if isinstance(value, Unit):
            value.x = x
            value.y = self.y
            value.prev_x = x
            value.prev_y = self.y
        self.grid.grid[self.y][x] = value


class GridManager:
    def __init__(self, grid_size):
        self.grid_size = grid_size
        self.grid: list[list[Union[None, Unit]]] = [[None for _ in range(grid_size)] for _ in range(grid_size)]
        self.balance: float = 0.0

    def __getitem__(self, index: int):
        if isinstance(index, int):
            return GridRow(self, index)
        else:
            raise TypeError("Invalid index type")

    def clear(self):
        self.grid = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]

    def move_unit(self, unit: Unit, x: int, y: int):
        unit.move_to(self.grid, x, y)

    def iter_unit(self):
        for row in self.grid:
            for unit in row:
                if unit is None:
                    continue
                yield unit

    def iter_cords(self):
        for y, row in enumerate(self.grid):
            for x, unit in enumerate(row):
                yield x, y

    @property
    def selected_units(self):
        return [i for i in self.iter_unit() if isinstance(i, White) and i.selected]

    def _bfs_assemble(self, start: tuple, unit: Unit, is_blocking: Union[None, Callable] = None):
        if not unit.target_cord:
            return [start]
        queue = [start]
        visited = {start}
        parent = {start: None}

        while queue:
            queue.sort(key=lambda x: math.hypot(x[0] - unit.target_cord[0], x[1] - unit.target_cord[1]))
            row, col = queue.pop(0)

            if (row, col) == unit.target_cord:
                # Target found, extract path
                path = []
                cord = (row, col)
                while cord is not None:
                    path.append(cord)
                    cord = parent[cord]
                path.reverse()
                return path

            for drow, dcol in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nrow, ncol = row + drow, col + dcol
                if not (0 <= nrow < self.grid_size and 0 <= ncol < self.grid_size):
                    continue
                if (nrow, ncol) in visited:
                    continue
                if is_blocking and is_blocking(self.grid[nrow][ncol]):
                    continue
                visited.add((nrow, ncol))
                parent[(nrow, ncol)] = (row, col)
                queue.append((nrow, ncol))

        return [start]

    def _bfs_enemy(self, start, unit) -> list[tuple[int, int]]:
        queue = [start]
        visited = {start}
        parent = {start: None}

        while queue:
            row, col = queue.pop(0)

            if (row, col) != start and self.grid[row][col] and type(self.grid[row][col]) is not type(unit):
                # Target found, extract path
                path = []
                cord = (row, col)
                while cord is not None:
                    path.append(cord)
                    cord = parent[cord]
                path.reverse()
                return path

            for drow, dcol in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nrow, ncol = row + drow, col + dcol
                if 0 <= nrow < self.grid_size and 0 <= ncol < self.grid_size and (nrow, ncol) not in visited \
                        and abs(nrow - start[0]) + abs(ncol - start[1]) <= unit.search_radius \
                        and type(self.grid[nrow][ncol]) is not type(unit):
                    visited.add((nrow, ncol))
                    parent[(nrow, ncol)] = (row, col)
                    queue.append((nrow, ncol))

        return [start]

    def bfs(self, start: tuple, unit: Unit):
        ret = self._bfs_assemble(start, unit, lambda u: isinstance(u, type(unit))
                                                        and (u.target_cord != unit.target_cord or
                                                             (u.target_cord == unit.target_cord and
                                                              (u.hp <= 0 or unit.move_timer < u.move_timer))))
        if len(ret) == 1:
            ret = self._bfs_assemble(start, unit, None)
        if len(ret) == 1:
            ret = self._bfs_enemy(start, unit)
        return ret

    def move_units(self, delta_time):
        # update timers
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                unit = self.grid[y][x]
                if isinstance(unit, Unit):
                    unit.update_time(delta_time)

        # resolve movement & eat
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                unit = self.grid[y][x]
                if not isinstance(unit, Unit):
                    continue
                if unit.hp <= 0:
                    continue
                if isinstance(unit.target_cord, tuple) and x == unit.target_cord[1] and y == unit.target_cord[0]:
                    unit.target_cord = None
                try:
                    target_y, target_x = self.bfs((y, x), unit)[1]
                except IndexError:
                    unit.target_cord = None
                    continue
                if target_y == y and target_x == x:
                    continue

                # if face to face deduct hp
                if isinstance(self.grid[target_y][target_x], Unit) \
                        and type(self.grid[target_y][target_x]) != type(unit):
                    self.fight(x, y, target_x, target_y)

                # if last hit "eat it"
                if self.can_eat(x, y, target_x, target_y):
                    self.move_unit(unit, target_x, target_y)

    def fight(self, x1: int, y1: int, x2: int, y2: int):
        u1 = self.grid[y1][x1]
        u2 = self.grid[y2][x2]
        if not isinstance(u1, Unit) or not isinstance(u2, Unit):
            return
        if u1.hp <= 0 or u2.hp <= 0:
            return
        if u2.atk_timer <= 0:
            u1.hp -= u2.dmg
            u2.atk_timer += u2.atk_cd
        if u1.atk_timer <= 0:
            u2.hp -= u1.dmg
            u1.atk_timer += u1.atk_cd

        balance_dict = {
            White: -1,
            Black: 1,
            Unit: 0
        }
        # print(f"fight! {u1} {u2}")
        # if equal fight, roll a dice
        if u1.hp <= 0 and u2.hp <= 0:
            sign = -1 if random.uniform(self.balance - 2, self.balance + 2) < 0 else 1
            survivor = None
            if balance_dict[type(u1)] == sign:
                survivor = u1
            if balance_dict[type(u2)] == sign:
                survivor = u2
            if isinstance(survivor, Unit):
                self.balance -= balance_dict[type(survivor)]
                survivor.hp = 1
            print(f"rolled dice {self.balance}")

    def can_eat(self, x1: int, y1: int, x2: int, y2: int):
        u1 = self.grid[y1][x1]
        u2 = self.grid[y2][x2]
        if u1.move_timer > 0:
            return False
        if not isinstance(u1, Unit):
            return False
        if not isinstance(u2, Unit):
            return True
        if type(u1) == type(u2):
            return False
        if u2.hp <= 0:
            return True
        if u1.move_timer <= 0 and u2.hp <= 0:
            return True

    def find_max_hp_target(self, _class) -> Union[tuple, None]:
        max_hp = -1
        location = (-1, -1)

        for j, row in enumerate(self.grid):
            for i, unit in enumerate(row):
                if not isinstance(unit, _class):
                    continue
                if unit.hp > max_hp:
                    max_hp = unit.hp
                    location = (i, j)

        if max_hp != -1:
            return location
        return None
