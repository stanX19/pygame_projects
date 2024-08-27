from __future__ import annotations

import math
import random
from typing import Union, Any, Callable

from .unit import Unit, Black, White, ClassEnum

UPGRADE_COST = 10

ENERGY_DICT: dict[Any, float] = {
    Black: UPGRADE_COST * 15,
    White: UPGRADE_COST * 15,
}


class GridRow:
    def __init__(self, grid, y: int):
        self.grid_manager = grid
        self.y = y
        self.y += self.grid_manager.grid_size * (self.y < 0)

    def __getitem__(self, col):
        return self.grid_manager.grid[self.y][col]

    def __setitem__(self, x: int, value: Union[None, Unit]):
        x += self.grid_manager.grid_size * (x < 0)
        if isinstance(value, Unit):
            value.x = x
            value.y = self.y
            value.prev_x = x
            value.prev_y = self.y
        self.grid_manager.grid[self.y][x] = value


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

    def count_if(self, func):
        return sum(1 for u in self.iter_unit() if func(u))

    def iter_cords(self):
        for y, row in enumerate(self.grid):
            for x, unit in enumerate(row):
                yield x, y

    def select_all(self, key=None):
        for u in self.iter_unit():
            if key and key(u):
                u.selected = True

    def unselect_all(self, key=None):
        for u in self.selected_units:
            if key and not key(u):
                continue
            u.selected = False

    @property
    def selected_units(self):
        return [i for i in self.iter_unit() if isinstance(i, White) and i.selected]

    def _extract_path(self, parent: dict, y: int, x: int):
        path = []
        cord = (y, x)
        while cord is not None:
            path.append(cord)
            cord = parent[cord]
        path.reverse()
        return path

    def _bfs(self, start, unit, is_blocking=None, find_enemy=True) -> list[tuple[int, int]]:
        if not find_enemy and unit.target_cord is None:
            return [start]
        queue = [start]
        visited = {start}
        parent = {start: None}

        while queue:
            if not find_enemy:
                queue.sort(key=lambda c: math.hypot(c[0] - unit.target_cord[0], c[1] - unit.target_cord[1]))
            y, x = queue.pop(0)

            if find_enemy and (y, x) != start and self.grid[y][x] and type(self.grid[y][x]) is not type(unit):
                return self._extract_path(parent, y, x)
            elif not find_enemy and (y, x) == unit.target_cord:
                return self._extract_path(parent, y, x)

            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ny, nx = y + dy, x + dx
                if not (0 <= ny < self.grid_size and 0 <= nx < self.grid_size):
                    continue
                if (ny, nx) in visited:
                    continue
                if find_enemy and abs(ny - start[0]) + abs(nx - start[1]) > unit.search_radius:
                    continue
                if is_blocking and is_blocking(self.grid[ny][nx]):
                    continue
                visited.add((ny, nx))
                parent[(ny, nx)] = (y, x)
                queue.append((ny, nx))

        return [start]

    def bfs(self, start: tuple, unit: Unit):
        def blocking(u: Unit):
            if not isinstance(u, type(unit)):
                return False
            if u.target_cord != unit.target_cord:
                return True
            # have same target but
            if u.hp <= 0 or unit.move_timer < u.move_timer:
                return True

        ret = self._bfs(start, unit, is_blocking=blocking, find_enemy=False)
        if len(ret) == 1:
            ret = self._bfs(start, unit, None, find_enemy=False)
        if len(ret) == 1:
            ret = self._bfs(start, unit, lambda u: type(u) is type(unit))
        if len(ret) == 1:
            ret = self._bfs(start, unit)
        return ret

    def update_delta_time(self, delta_time):
        # update timers
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                unit = self.grid[y][x]
                if isinstance(unit, Unit):
                    unit.update_time(delta_time)

    def move_all_units(self):
        # resolve movement & eat
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                unit = self.grid[y][x]
                if not isinstance(unit, Unit):
                    continue
                if unit.hp <= 0 and unit.move_timer == 0:
                    self.grid[y][x] = None
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
        u1.attack(u2)
        u2.attack(u1)

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

        u1.update_class()
        u2.update_class()

    def can_eat(self, x1: int, y1: int, x2: int, y2: int):
        u1 = self.grid[y1][x1]
        u2 = self.grid[y2][x2]
        if not isinstance(u1, Unit) or u1.move_timer > 0 or u1.hp <= 0:
            return False
        if type(u1) == type(u2):
            return False
        if isinstance(u2, type(None)):
            return True
        if u1.move_timer <= 0 and u2.hp <= 0:
            return True

    def upgrade_unit_at(self, x, y, _class):
        unit = self.grid[y][x]
        if not isinstance(unit, Unit) and ENERGY_DICT[_class] >= 10:
            self[y][x] = _class(search_radius=self.grid_size)
            ENERGY_DICT[_class] -= 10
        elif isinstance(unit, _class):
            self.upgrade_unit(unit)

    def spawn_one_around(self, unit: Unit):
        if not isinstance(unit, (Black, White)):
            return

        def is_same_class(cord):
            return isinstance(self.grid[cord[1]][cord[0]], type(unit))

        def is_base(cord):
            _unit = self.grid[cord[1]][cord[0]]
            return is_same_class(cord) and _unit.unit_class is ClassEnum.BASE

        def is_upgradable(cord):
            _unit = self.grid[cord[1]][cord[0]]
            if _unit is None:
                return True
            if is_same_class(cord) and _unit.unit_class is not ClassEnum.BASE:
                return True
            return False

        # is_path can change to is_base to ensure is upgraded to base first
        targets = self.search_all_that((unit.x, unit.y), is_path=is_same_class, is_target=is_upgradable)
        best_cord = None
        min_score = float('inf')
        for x, y in targets:
            score = (abs(unit.x - x) + abs(unit.y - y))
            if not (0 <= x < self.grid_size and 0 <= y < self.grid_size):
                continue
            elif isinstance(self.grid[y][x], type(unit)):
                score += self.grid[y][x].hp
            elif isinstance(self.grid[y][x], Unit):
                continue
            if score < min_score:
                best_cord = (x, y)
                min_score = score

        if best_cord is not None:
            self.upgrade_unit_at(*best_cord, type(unit))

    def search_all_that(self, start: tuple[int, int], is_path: Callable[[tuple[int, int]], bool],
                        is_target: Callable[[tuple[int, int]], bool]):
        if start is None:
            return
        visited = {start}
        ret: list[tuple[int, int]] = []
        stack = [start]
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        while stack:
            cord = stack.pop(0)
            for dy, dx in directions:
                y, x = cord[1] + dy, cord[0] + dx
                if y < 0 or y >= self.grid_size or x < 0 or x >= self.grid_size:
                    continue
                curr = (x, y)
                if is_target(curr):
                    ret.append(curr)
                if curr not in visited and is_path(curr):
                    stack.append(curr)
                    visited.add(curr)

        return ret

    def spawn_units(self, white_rad=3, black_rad=100):
        for unit in self.iter_unit():
            if unit.unit_class == ClassEnum.BASE and unit.atk_timer == 0:
                ENERGY_DICT[type(unit)] += UPGRADE_COST
                unit.atk_timer = unit.atk_cd

    def upgrade_unit(self, unit: Unit):
        if not isinstance(unit, Unit):
            return
        if unit.unit_class == ClassEnum.BASE:
            self.spawn_one_around(unit)
        elif ENERGY_DICT[type(unit)] >= UPGRADE_COST:
            ENERGY_DICT[type(unit)] -= UPGRADE_COST
            unit._upgrade()
        else:
            return False
        return True

    def find_max_hp_target(self, _class) -> Union[Unit, None]:
        max_hp = 0
        ret = None

        for unit in self.iter_unit():
            if not isinstance(unit, _class):
                continue
            if unit.hp > max_hp:
                max_hp = unit.hp
                ret = unit

        return ret
