import math
import random

import pygame
from classes.grid_manager import GridManager, ENERGY_DICT
from classes.unit import Black, White, ClassEnum

# Initialize Pygame
pygame.init()

# Constants
GRID_SIZE = 12
BOARD_SIZE = 720
CELL_SIZE = BOARD_SIZE // GRID_SIZE
SIDE_SPACE = 300  # Space on the left and right of the board
SCREEN_WIDTH = BOARD_SIZE + SIDE_SPACE * 2
SCREEN_HEIGHT = BOARD_SIZE
LINE_WIDTH = 2
LINE_COLOR = (0, 0, 0)
BACKGROUND_COLOR = (0, 128, 0)  # Green background
LINE_MARGIN = LINE_WIDTH // 2  # Margin for line detection
ENERGY_RECOVERY_RATE = 0.1  # Energy recovery per second per unit
MAX_ENERGY = GRID_SIZE * 4 * 10  # Maximum energy

unit_nu_font = pygame.font.SysFont("consolas", CELL_SIZE // 2, bold=True, italic=False)
unit_nu_font_small = pygame.font.SysFont("consolas", CELL_SIZE // 4, bold=True, italic=False)
info_font = pygame.font.SysFont("consolas", 24, bold=True, italic=False)


class ReversiGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Reversi Board")
        self.grid = GridManager(GRID_SIZE)
        self.running: bool = True
        self.quit: bool = False
        self.clock = pygame.time.Clock()  # For delta time
        self.init_game()

    def init_game(self):
        self.running: bool = True
        self.quit: bool = False
        ENERGY_DICT[White] = 150
        ENERGY_DICT[Black] = 150
        # headquarters, 5 health, can fight back (1), delay: 1, range=melee
        self.grid.clear()
        # for i in range(GRID_SIZE):
        #     self.grid[i][0] = White(1, 1, 1, 100)
        #     self.grid[i][1] = White(1, 1, 1, 100)
        #     self.grid[i][-1] = Black(1, 1, 1, 100)
        #     self.grid[i][-2] = Black(1, 1, 1, 100)
        self.grid[-1][0] = White(5)
        self.grid[-3][0] = White(3)
        self.grid[-1][2] = White(3)
        # self.grid[-3][1] = White(4)
        # self.grid[-2][2] = White(4)
        self.grid[0][-1] = Black(5)
        self.grid[0][-3] = Black(3)
        self.grid[2][-1] = Black(3)  # self.grid[1][-3] = Black(4)  # self.grid[2][-2] = Black(4)

    def draw_grid(self):
        for x in range(SIDE_SPACE, BOARD_SIZE + SIDE_SPACE + 1, CELL_SIZE):
            pygame.draw.line(self.screen, LINE_COLOR, (x, 0), (x, BOARD_SIZE), LINE_WIDTH)
        for y in range(0, BOARD_SIZE, CELL_SIZE):
            pygame.draw.line(self.screen, LINE_COLOR, (SIDE_SPACE, y), (BOARD_SIZE + SIDE_SPACE, y), LINE_WIDTH)

    def get_grid_position(self, pos):
        x, y = pos
        if x < SIDE_SPACE or x >= BOARD_SIZE + SIDE_SPACE or y < 0 or y > BOARD_SIZE:
            return -1, -1
        x -= SIDE_SPACE
        if x % CELL_SIZE < LINE_MARGIN or x % CELL_SIZE > CELL_SIZE - LINE_MARGIN:
            return -1, -1
        if y % CELL_SIZE < LINE_MARGIN or y % CELL_SIZE > CELL_SIZE - LINE_MARGIN:
            return -1, -1
        row = y // CELL_SIZE
        col = x // CELL_SIZE
        return row, col

    # def place_basic_unit(self, y, x):
    #     if self.white_energy < BASIC_UNIT_COST:
    #         return
    #     self.white_energy -= BASIC_UNIT_COST
    #     if 0 <= y < GRID_SIZE and 0 <= x < GRID_SIZE:
    #         self.grid[y][x] = White(search_radius=GRID_SIZE)

    def draw_units(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                unit = self.grid[y][x]
                if not unit:
                    continue
                n = min(0.1, unit.move_cd)  # animation time cannot be more than n
                if unit.move_timer == float('inf'):
                    k = 1
                else:
                    k = max(0, min(1, (unit.move_cd - unit.move_timer) / n))  # how much towards current
                    k = k ** 2
                _x = k * x + (1 - k) * unit.prev_x
                _y = k * y + (1 - k) * unit.prev_y
                center = (_x * CELL_SIZE + CELL_SIZE // 2 + SIDE_SPACE, _y * CELL_SIZE + CELL_SIZE // 2)
                center = (math.ceil(center[0]), math.ceil(center[1]))
                radius = CELL_SIZE // 2 - LINE_MARGIN
                pygame.draw.circle(self.screen, unit.color, center, radius)

                hp_number = unit_nu_font.render(str(math.ceil(unit.hp)), True, unit.contrast_color)
                hp_rect = hp_number.get_rect(center=center)
                dmg_number = unit_nu_font_small.render(str(math.ceil(unit.dmg)), True, (128, 128, 128))
                dmg_rect = dmg_number.get_rect(center=center)
                dmg_rect.left = hp_rect.right
                dmg_rect.y += CELL_SIZE // 8

                # dmg first
                self.screen.blit(dmg_number, dmg_rect)
                self.screen.blit(hp_number, hp_rect)

                if unit.selected:
                    pygame.draw.circle(self.screen, (0, 255, 255), center, radius, width=2)

    def draw_info(self):
        info_text = info_font.render(f"""Energy left: {ENERGY_DICT[White]:<6.0f}""", True, (255, 255, 255))
        info_rect = info_text.get_rect()
        info_rect.left = 50
        info_rect.bottom = BOARD_SIZE - 100
        self.screen.blit(info_text, info_rect)
        info_text = info_font.render(f"""Energy left: {ENERGY_DICT[Black]:<.0f}""", True, (255, 255, 255))
        info_rect = info_text.get_rect()
        info_rect.left = SIDE_SPACE + BOARD_SIZE + 50
        info_rect.top = 100
        self.screen.blit(info_text, info_rect)

    def draw_end_game(self, msg):
        info_text = info_font.render(msg, True, (255, 255, 255))
        info_rect = info_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(info_text, info_rect)

    def black_play(self):
        if random.random() > 0.05:
            return
        white_fighters = [i for i in self.grid.iter_unit() if
                          isinstance(i, White) and i.unit_class is not ClassEnum.BASE]
        black_fighters = [i for i in self.grid.iter_unit() if
                          isinstance(i, Black) and i.unit_class is not ClassEnum.BASE]
        black_bases = [i for i in self.grid.iter_unit() if
                       isinstance(i, Black) and i.unit_class is ClassEnum.BASE]
        if len(black_fighters) - len(white_fighters) > len(black_bases):
            target = sorted(black_fighters, key=lambda u: u.hp)[-1]
        elif black_bases:
            target = black_bases[-1]
        elif black_fighters:
            target = black_fighters[-1]
        else:
            target = None
        self.grid.upgrade_unit(target)

    def recover_energy(self, delta_time):
        white_count = 10 + sum(u.hp - 4 for u in self.grid.iter_unit() if isinstance(u, White) and u.hp >= 5)
        black_count = 10 + sum(u.hp - 4 for u in self.grid.iter_unit() if isinstance(u, Black) and u.hp >= 5)
        white_rate = ENERGY_RECOVERY_RATE * white_count
        black_rate = ENERGY_RECOVERY_RATE * black_count
        ENERGY_DICT[White] = min(MAX_ENERGY, ENERGY_DICT[White] + white_rate * delta_time)
        ENERGY_DICT[Black] = min(MAX_ENERGY, ENERGY_DICT[Black] + black_rate * delta_time)

    def handle_mouse_event(self, event):
        pos = pygame.mouse.get_pos()
        y, x = self.get_grid_position(pos)
        if y == -1 or x == -1:
            return
        if isinstance(self.grid[y][x], White) and event.button == 3:
            if self.grid[y][x].selected:
                for u in self.grid.selected_units:
                    self.grid.upgrade_unit(u)
            else:
                self.grid.upgrade_unit(self.grid[y][x])
        elif event.button == 1 and not isinstance(self.grid[y][x], White) and self.grid.selected_units:
            for u in self.grid.selected_units:
                u.target_cord = (y, x)
        # elif event.button == 1 and self.grid[y][x] is None:
        #     self.place_basic_unit(y, x)
        elif event.button == 1 and isinstance(self.grid[y][x], White):
            if not pygame.key.get_pressed()[pygame.K_LCTRL]:
                self.grid.unselect_all()
            self.grid[y][x].selected = True

    def check_end_game(self):
        count = {Black: 0, White: 0, type(None): 0}
        for u in self.grid.iter_unit():
            count[type(u)] += 1
        if count[White] == 0:
            self.draw_end_game(f"""YOU LOST""")
            self.running = False
        if count[Black] == 0:
            self.draw_end_game(f"""YOU WON!""")
            self.running = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit = True
            elif event.type == pygame.MOUSEBUTTONUP:
                self.handle_mouse_event(event)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LCTRL] and keys[pygame.K_a]:
            self.grid.select_all(key=lambda u: isinstance(u, White))
        if keys[pygame.K_ESCAPE]:
            self.grid.unselect_all()

    def run(self):
        self.init_game()
        self.running = True
        while self.running and not self.quit:
            delta_time = self.clock.tick(60) / 1000.0  # Get delta time
            self.handle_events()

            self.grid.update_delta_time(delta_time)
            self.grid.spawn_units()
            self.grid.move_all_units()
            self.recover_energy(delta_time)
            self.black_play()

            self.screen.fill(BACKGROUND_COLOR)
            self.draw_grid()
            self.draw_units()
            self.draw_info()
            self.check_end_game()
            pygame.display.flip()

        self.running = True
        while self.running and not self.quit:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit = True
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.running = False
        if self.quit:
            return -1
        return 0


def main():
    game = ReversiGame()
    while game.run() == 0:
        pass


if __name__ == '__main__':
    main()
