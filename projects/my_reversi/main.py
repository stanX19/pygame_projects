import random
import sys
from collections import deque
from typing import Union
import pygame

# Initialize Pygame
pygame.init()

# Constants
BOARD_SIZE = 800
GRID_SIZE = 8
CELL_SIZE = BOARD_SIZE // GRID_SIZE
LINE_WIDTH = 2
LINE_COLOR = (0, 0, 0)
BACKGROUND_COLOR = (0, 128, 0)  # Green background
LINE_MARGIN = LINE_WIDTH // 2  # Margin for line detection
SIDE_SPACE = 300  # Space on the left and right of the board
ENERGY_RECOVERY_RATE = 2.5  # Energy recovery per second
MAX_ENERGY = 50  # Maximum energy
BASIC_UNIT_COST = 10  # Energy cost to spawn a unit
UPGRADE_UNIT_COST = 20  # Energy cost to upgrade a unit

unit_nu_font = pygame.font.SysFont("consolas", 32, bold=True, italic=False)
info_font = pygame.font.SysFont("consolas", 24, bold=True, italic=False)

class Unit:
    def __init__(self, color: tuple, hp: float, dmg: float, move_cd: float, search_radius: float):
        self.color: tuple = color
        self.contrast_color: tuple = (255 - color[0], 255 - color[1], 255 - color[2])
        self.hp: float = hp
        self.dmg: float = dmg
        self.move_cd: float = move_cd
        self.search_radius: float = search_radius
        self._move_timer: float = move_cd
        self._atk_timer: float = move_cd

    @property
    def move_timer(self):
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
        if self.move_cd == float('inf'):
            return
        self._atk_timer = max(0, val)

    def update_time(self, delta_time):
        self.atk_timer -= delta_time
        self.move_timer -= delta_time

    def __str__(self):
        return f"{self.__class__}[hp={self.hp}, dmg={self.dmg}, cd={self.move_timer:.2f}]"

    def __repr__(self):
        return self.__str__()


class Black(Unit):
    def __init__(self, hp: float, dmg: float, move_cd: float, search_radius: float):
        super().__init__((0, 0, 0), hp, dmg, move_cd, search_radius)  # Black


class White(Unit):
    def __init__(self, hp: float, dmg: float, move_cd: float, search_radius: float):
        super().__init__((255, 255, 255), hp, dmg, move_cd, search_radius)  # White


class ReversiGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((BOARD_SIZE + 2 * SIDE_SPACE, BOARD_SIZE))
        pygame.display.set_caption("Reversi Board")
        self.grid: list[list[Union[None, Unit]]] = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.running = True
        self.clock = pygame.time.Clock()  # For delta time
        self.balance = 0.0
        self.energy = MAX_ENERGY
        self.black_energy = MAX_ENERGY
        self.init_game()

    def init_game(self):
        # headquarters, 5 health, can fight back (1), delay: 1, range=melee
        self.grid[GRID_SIZE - 1][0] = White(5, 1, 1, 1)
        self.grid[0][GRID_SIZE - 1] = Black(5, 1, 1, 1)

    def draw_grid(self):
        for x in range(SIDE_SPACE, BOARD_SIZE + SIDE_SPACE + 1, CELL_SIZE):
            pygame.draw.line(self.screen, LINE_COLOR, (x, 0), (x, BOARD_SIZE), LINE_WIDTH)
        for y in range(0, BOARD_SIZE, CELL_SIZE):
            pygame.draw.line(self.screen, LINE_COLOR, (SIDE_SPACE, y), (BOARD_SIZE + SIDE_SPACE, y), LINE_WIDTH)

    def get_grid_position(self, pos):
        x, y = pos
        if x < SIDE_SPACE or x >= BOARD_SIZE + SIDE_SPACE:
            return -1, -1
        x -= SIDE_SPACE
        if x % CELL_SIZE < LINE_MARGIN or x % CELL_SIZE > CELL_SIZE - LINE_MARGIN:
            return -1, -1
        if y % CELL_SIZE < LINE_MARGIN or y % CELL_SIZE > CELL_SIZE - LINE_MARGIN:
            return -1, -1
        row = y // CELL_SIZE
        col = x // CELL_SIZE
        return row, col

    def place_unit(self, row, col, unit):
        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
            self.grid[row][col] = unit

    def bfs(self, start, unit) -> tuple[int, int]:
        queue = deque([start])
        visited = {start}
        while queue:
            row, col = queue.popleft()
            if (row, col) != start and self.grid[row][col] and type(self.grid[row][col]) is not type(unit):
                return row, col

            for drow, dcol in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nrow, ncol = row + drow, col + dcol
                if 0 <= nrow < GRID_SIZE and 0 <= ncol < GRID_SIZE and (nrow, ncol) not in visited \
                        and abs(nrow - start[0]) + abs(ncol - start[1]) <= unit.search_radius \
                        and type(self.grid[nrow][ncol]) is not type(unit):
                    visited.add((nrow, ncol))
                    queue.append((nrow, ncol))
        return start

    def norm_target_cord(self, target_row, target_col, row, col) -> tuple[int, int]:
        target_col -= col
        target_row -= row
        if target_row and target_col:
            if abs(target_row) > abs(target_col):
                target_col = 0
            else:
                target_row = 0
        if target_row < 0:
            target_row = -1
        elif target_row > 0:
            target_row = 1
        if target_col < 0:
            target_col = -1
        elif target_col > 0:
            target_col = 1
        return row + target_row, col + target_col

    def move_units(self, delta_time):
        # update timers
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                unit = self.grid[row][col]
                if isinstance(unit, Unit):
                    unit.update_time(delta_time)

        # resolve movement & eat
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                unit = self.grid[row][col]
                if not isinstance(unit, Unit):
                    continue
                if unit.hp <= 0:
                    continue
                if unit.move_timer > 0 or unit.move_timer is None:
                    continue
                target_row, target_col = self.bfs((row, col), unit)
                if target_row == row and target_col == col:
                    continue
                target_row, target_col = self.norm_target_cord(target_row, target_col, row, col)

                # if face to face deduct hp
                if isinstance(self.grid[target_row][target_col], Unit) \
                        and type(self.grid[target_row][target_col]) != type(unit):
                    self.fight(col, row, target_col, target_row)

                # if last hit "eat it"
                if self.can_eat(col, row, target_col, target_row):
                    self.grid[row][col] = None
                    self.grid[target_row][target_col] = unit
                    unit.move_timer = unit.move_cd

    def fight(self, x1: int, y1: int, x2: int, y2: int):
        u1 = self.grid[y1][x1]
        u2 = self.grid[y2][x2]
        if not isinstance(u1, Unit) or not isinstance(u2, Unit):
            return
        if u2.atk_timer > 0 or u1.atk_timer > 0:
            return
        if u2.atk_timer <= 0:
            u1.hp -= u2.dmg
            u2.atk_timer += u2.move_cd
        if u1.atk_timer <= 0:
            u2.hp -= u1.dmg
            u1.atk_timer += u1.move_cd

        balance_dict = {
            White: -1,
            Black: 1,
            Unit: 0
        }
        print(f"fight! {u1} {u2}")
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
        if not isinstance(u1, Unit):
            return False
        if not isinstance(u2, Unit):
            return True
        if type(u1) == type(u2):
            return False
        if u2.hp <= 0:
            return True
        if u1.move_timer > 0:
            return False
        if u1.move_timer <= 0 and u2.hp <= 0:
            return True

    def draw_units(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                unit = self.grid[y][x]
                if not unit:
                    continue
                center = (x * CELL_SIZE + CELL_SIZE // 2 + SIDE_SPACE, y * CELL_SIZE + CELL_SIZE // 2)
                radius = CELL_SIZE // 2 - LINE_MARGIN
                pygame.draw.circle(self.screen, unit.color, center, radius)
                number = unit_nu_font.render(str(unit.hp), True, unit.contrast_color)
                nu_rect = number.get_rect(center=center)
                self.screen.blit(number, nu_rect)

    def draw_info(self):
        info_text = info_font.render(f"""Energy left: {self.energy:<6.2f}""", True, (255, 255, 255))
        info_rect = info_text.get_rect()
        info_rect.left = 50
        info_rect.bottom = BOARD_SIZE - 100
        self.screen.blit(info_text, info_rect)
        info_text = info_font.render(f"""Energy left: {self.black_energy:<.2f}""", True, (255, 255, 255))
        info_rect = info_text.get_rect()
        info_rect.left = SIDE_SPACE + BOARD_SIZE + 50
        info_rect.top = 100
        self.screen.blit(info_text, info_rect)

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

    def spawn_black_unit(self, delta_time):
        if self.black_energy < BASIC_UNIT_COST:
            return
        self.black_energy -= BASIC_UNIT_COST
        loc = self.find_max_hp_target(Black)
        if loc is None:
            return
        if self.grid[loc[1]][loc[0]].hp <= 1:
            return
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            y, x = loc[1] + dy, loc[0] + dx
            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE and not self.grid[y][x]:
                self.grid[y][x] = Black(1, 1, 1, GRID_SIZE ** 2)
                break

    def recover_energy(self, delta_time):
        self.energy = min(MAX_ENERGY, self.energy + ENERGY_RECOVERY_RATE * delta_time)
        self.black_energy = min(MAX_ENERGY, self.black_energy + ENERGY_RECOVERY_RATE * delta_time)

    def handle_mouse_event(self, event):
        pos = pygame.mouse.get_pos()
        y, x = self.get_grid_position(pos)
        if y == -1 or x == -1:
            return
        if isinstance(self.grid[y][x], White) and event.button == 3 and self.energy >= UPGRADE_UNIT_COST:
            self.energy -= UPGRADE_UNIT_COST
            self.grid[y][x].hp += 1
            self.grid[y][x].dmg = self.grid[y][x].hp
        elif event.button == 1 and self.grid[y][x] is None and self.energy >= BASIC_UNIT_COST:
            self.energy -= BASIC_UNIT_COST
            self.place_unit(y, x, White(1, 1, 1, 4))

    def run(self):
        while self.running:
            delta_time = self.clock.tick(60) / 1000.0  # Get delta time
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse_event(event)

            self.move_units(delta_time)
            self.recover_energy(delta_time)
            self.spawn_black_unit(delta_time)

            self.screen.fill(BACKGROUND_COLOR)
            self.draw_grid()
            self.draw_units()
            self.draw_info()
            pygame.display.flip()

        pygame.quit()
        sys.exit()


# Create and run the game
game = ReversiGame()
game.run()
