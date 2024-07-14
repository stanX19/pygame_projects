from typing import Union


class Unit:
    def __init__(self, color: tuple,
                 hp: float, dmg: float, move_cd: float, search_radius: float):
        self.color: tuple = color
        self.contrast_color: tuple = (255 - color[0], 255 - color[1], 255 - color[2])
        self.x: int = -1
        self.y: int = -1
        self.prev_x: int = self.x
        self.prev_y: int = self.y
        self.hp: float = hp
        self.dmg: float = dmg
        self.move_cd: float = move_cd
        self.atk_cd: float = move_cd
        self.search_radius: float = search_radius
        self._move_timer: float = self.move_cd * 2
        self._atk_timer: float = self.move_cd * 2
        self.selected: bool = False
        self.target_cord: Union[None, tuple[int, int]] = None

    def move_to(self, grid: list[list], x: int, y: int):
        self.prev_x = self.x
        self.prev_y = self.y
        self.x = x
        self.y = y
        grid[self.prev_y][self.prev_x] = None
        grid[self.y][self.x] = self
        self.move_timer = self.move_cd

    @property
    def move_timer(self) -> float:
        return self._move_timer

    @move_timer.setter
    def move_timer(self, val):
        if self.move_cd == float('inf'):
            return
        self._move_timer = max(0, val)

    @property
    def atk_timer(self):
        return self._atk_timer

    @atk_timer.setter
    def atk_timer(self, val):
        if self.atk_cd == float('inf'):
            return
        self._atk_timer = max(0, val)

    def update_time(self, delta_time):
        self.atk_timer -= delta_time
        self.move_timer -= delta_time

    def upgrade(self):
        self.hp += 1
        # self.dmg += 1

    def __str__(self):
        return f"{self.__class__}[hp={self.hp}, dmg={self.dmg}\
, mv_cd={self.move_timer:.2f}, atk_cd={self.atk_timer:.2f}]"

    def __repr__(self):
        return self.__str__()


class Black(Unit):
    def __init__(self, hp: float = 1, dmg: float = 1,
                 move_cd: float = 1, search_radius: float = 2):
        super().__init__((0, 0, 0), hp, dmg, move_cd, search_radius)


class White(Unit):
    def __init__(self, hp: float = 1, dmg: float = 1,
                 move_cd: float = 1, search_radius: float = 2):
        super().__init__((255, 255, 255), hp, dmg, move_cd, search_radius)
