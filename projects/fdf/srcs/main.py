import math

import pygame

# Initialize Pygame
pygame.init()

# Set up display
WIDTH, HEIGHT = 1200, 600
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Coordinate Grid')

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# types
t_vec4 = list[int, int, int, int]
t_vec2 = list[int, int]
t_mat = list[t_vec4, t_vec4, t_vec4, t_vec4]


# grid def
def get_grid() -> list[list[t_vec4]]:
    grid = [
        [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        [10, 20, 20, 20, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        [10, 10, 30, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        [10, 20, 20, 20, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        [10, 20, 20, 20, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        [10, 20, 20, 20, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        [10, 20, 20, 20, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        [10, 20, 20, 20, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        [10, 20, 20, 20, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 100, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        [10, 10, 10, 10, 10, 10, 100, 100, 100, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        [10, 10, 10, 50, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        [10, 10, 10, 50, 10, 10, 100, 100, 100, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        [10, 10, 10, 50, 50, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        [10, 10, 10, 50, 100, 100, 100, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
    ]
    GAP = min(WIDTH, HEIGHT) / max(len(grid), len(grid[0])) / 2
    DISPLACE = 0
    mid_x = len(grid) // 2
    mid_y = len(grid[0]) // 2
    return [[[(x - mid_x) * GAP + DISPLACE, (y - mid_y) * GAP + DISPLACE, z, 1]
             for x, z in enumerate(row)] for y, row in enumerate(grid)]


transform_mat: t_mat = [
    [1, 0, 0, WIDTH // 2],
    [0, 1, 0, HEIGHT // 2],
    [0, 0, 1, 0],
    [0, 0, 0, 1],
]


def matrix_matrix_mult(m1: t_mat, m2: t_mat) -> t_mat:
    m3 = [[0 for _ in range(len(m2[0]))] for _ in range(len(m1))]
    for i in range(len(m1)):
        for j in range(len(m2[0])):
            for k in range(len(m2)):
                m3[i][j] += m1[i][k] * m2[k][j]
    return m3


def matrix_vec_mult(matrix: t_mat, vector: t_vec4) -> t_vec4:
    new_vector = [0 for _ in vector]
    for i, row in enumerate(matrix):
        for j, val in enumerate(row):
            new_vector[i] += val * vector[j]
    return new_vector


def vec_to_xy(v: t_vec4) -> t_vec2:
    v2 = matrix_vec_mult(transform_mat, v)
    return [v2[0], HEIGHT - v2[1]]


def draw_square(c1: t_vec2, c2: t_vec2, c3: t_vec2, c4: t_vec2):
    pygame.draw.polygon(WINDOW, WHITE, [c1, c2, c3], width=2)
    pygame.draw.polygon(WINDOW, WHITE, [c2, c3, c4], width=2)


# Function to draw grid
def draw_grid(grid: list[list[t_vec4]]) -> None:
    grid = [[vec_to_xy(v) for v in line] for line in grid]
    for y, row in enumerate(grid):
        for x, c1 in enumerate(row):
            if x != 0 and y != 0:
                draw_square(grid[y - 1][x - 1], grid[y][x - 1], grid[y - 1][x], c1)


def create_translation_matrix(x, y, z) -> t_mat:
    return [
        [1, 0, 0, x],
        [0, 1, 0, y],
        [0, 0, 1, z],
        [0, 0, 0, 1],
    ]


def apply_at_center(mat: t_mat) -> t_mat:
    trans1 = create_translation_matrix(- WIDTH / 2, - HEIGHT / 2, 0)
    trans2 = create_translation_matrix(WIDTH / 2, HEIGHT / 2, 0)
    return matrix_matrix_mult(trans2, matrix_matrix_mult(mat, trans1))


def create_zoom_matrix(zoom_factor) -> t_mat:
    zoom = [
        [zoom_factor, 0, 0, 0],
        [0, zoom_factor, 0, 0],
        [0, 0, zoom_factor, 0],
        [0, 0, 0, 1],
    ]
    return apply_at_center(zoom)


def create_rotation_matrix_x(angle) -> t_mat:
    cos_theta = math.cos(angle)
    sin_theta = math.sin(angle)
    return apply_at_center([
        [1, 0, 0, 0],
        [0, cos_theta, -sin_theta, 0],
        [0, sin_theta, cos_theta, 0],
        [0, 0, 0, 1],
    ])


def create_rotation_matrix_y(angle) -> t_mat:
    cos_theta = math.cos(angle)
    sin_theta = math.sin(angle)
    return apply_at_center([
        [cos_theta, 0, sin_theta, 0],
        [0, 1, 0, 0],
        [-sin_theta, 0, cos_theta, 0],
        [0, 0, 0, 1],
    ])


def create_rotation_matrix_z(angle) -> t_mat:
    cos_theta = math.cos(angle)
    sin_theta = math.sin(angle)
    return apply_at_center([
        [cos_theta, -sin_theta, 0, 0],
        [sin_theta, cos_theta, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ])


def main():
    global transform_mat
    grid = get_grid()
    running = True
    last_mouse_pos = None

    while running:
        zoom_factor = 1
        trans_x, trans_y, trans_z = 0, 0, 0
        angle_x, angle_y, angle_z = 0, 0, 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0]:  # Left mouse button is pressed
                    if last_mouse_pos:
                        dx, dy = event.pos[0] - last_mouse_pos[0], event.pos[1] - last_mouse_pos[1]
                        if dx:
                            angle_y += dx * 0.01  # Adjust sensitivity as needed
                        else:
                            angle_x += dy * 0.01  # Adjust sensitivity as needed
                    last_mouse_pos = event.pos
                else:
                    last_mouse_pos = None
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # Scroll up
                    zoom_factor *= 1.1
                elif event.button == 5:  # Scroll down
                    zoom_factor /= 1.1

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            trans_y -= 10
        if keys[pygame.K_s]:
            trans_y += 10
        if keys[pygame.K_a]:
            trans_x += 10
        if keys[pygame.K_d]:
            trans_x -= 10
        if keys[pygame.K_UP]:
            angle_x -= 0.01
        if keys[pygame.K_DOWN]:
            angle_x += 0.01
        if keys[pygame.K_LEFT]:
            angle_y -= 0.01
        if keys[pygame.K_RIGHT]:
            angle_y += 0.01
        if keys[pygame.K_z]:
            angle_z += 0.01
        if keys[pygame.K_x]:
            angle_z -= 0.01
        # print(trans_x, trans_y, trans_z)

        transform_mat = matrix_matrix_mult(create_zoom_matrix(zoom_factor), transform_mat)
        transform_mat = matrix_matrix_mult(create_rotation_matrix_x(angle_x), transform_mat)
        transform_mat = matrix_matrix_mult(create_rotation_matrix_y(angle_y), transform_mat)
        transform_mat = matrix_matrix_mult(create_rotation_matrix_z(angle_z), transform_mat)
        transform_mat = matrix_matrix_mult(create_translation_matrix(trans_x, trans_y, trans_z), transform_mat)
        # print(transform_mat)
        WINDOW.fill(BLACK)
        draw_grid(grid)
        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    main()
