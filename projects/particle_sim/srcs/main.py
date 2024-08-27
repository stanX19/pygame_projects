import pygame
import random
import math
from particle import Particle
from particle_collision import *
from collections import deque

WIDTH, HEIGHT = 700, 700
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


def dot_product(v1, v2):
    return sum(a * b for a, b in zip(v1, v2))


class ParticleHandler:
    def __init__(self, width, height):
        self.particles: list[Particle] = []
        self.width = width
        self.height = height
        self.grid_size = 0
        self.grid: list[list[list[Particle]]] = []

    def generate_grid(self):
        self.grid_size = max(p.rad for p in self.particles) * 2
        grid_width = math.ceil(self.width / self.grid_size)
        grid_height = math.ceil(self.height / self.grid_size)
        self.grid = [[[] for _ in range(grid_width)] for _ in range(grid_height)]

    def grid_coordinates(self, particle):
        x_idx = int(particle.x / self.grid_size)
        y_idx = int(particle.y / self.grid_size)
        return x_idx, y_idx

    def assign_particles_to_grid(self):
        self.generate_grid()
        for particle in self.particles:
            x_idx, y_idx = self.grid_coordinates(particle)
            if 0 <= x_idx < len(self.grid[0]) and 0 <= y_idx < len(self.grid):
                self.grid[y_idx][x_idx].append(particle)

    def get_total_momentum(self):
        return sum(p.momentum[0] for p in self.particles) + sum(p.momentum[1] for p in self.particles)

    def get_total_ke(self):
        return sum(p.kinetic_energy for p in self.particles)

    def add_particle(self, particle):
        self.particles.append(particle)

    def update_particles(self):
        for particle in self.particles:
            print(particle.x, particle.y, particle.xv, particle.yv)
            particle.move()

    def draw_particles(self, surface):
        for particle in self.particles:
            particle.draw(surface)

    def get_neighbors(self, x, y):
        # Get neighboring grid coordinates, including diagonals
        neighbors = []
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue  # Skip the current cell
                nx, ny = x + dx, y + dy
                if 0 <= nx < len(self.grid[0]) and 0 <= ny < len(self.grid):
                    neighbors.append((nx, ny))
        return neighbors

    def collide_all(self):
        # Step 1: Assign particles to grids
        self.assign_particles_to_grid()

        # Step 2: Initialize a stack to track grids needing further collision checks
        stack = deque((x, y) for y in range(len(self.grid)) for x in range(len(self.grid[y])))

        # Step 4: Process the stack until no grids are marked as True
        while stack:
            x, y = stack.pop()
            particles_in_grid: list[Particle] = self.grid[y][x]

            collided_grids = set()
            for i, p1 in enumerate(particles_in_grid):
                if p1.wall_bound(self.width, self.height):
                    collided_grids.add((x, y))
                for j, p2 in enumerate(particles_in_grid[i + 1:]):
                    if particle_collision(p1, p2):
                        collided_grids.add((x, y))

            for nx, ny in self.get_neighbors(x, y):
                neighboring_particles = self.grid[ny][nx]
                for p1 in particles_in_grid:
                    for p2 in neighboring_particles:
                        if particle_collision(p1, p2):
                            collided_grids.add((x, y))
                            collided_grids.add((nx, ny))

            stack.extend(collided_grids)

    def apply_gravity(self):
        for p in self.particles:
            p.yv += 0.1


# Game class
class Game:
    def __init__(self):
        pygame.init()
        self.running = True
        self.clock = pygame.time.Clock()
        self.particle_handler = ParticleHandler(WIDTH, HEIGHT)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.font = pygame.font.Font(None, 36)
        pygame.display.set_caption("Particle System with Collisions")
        self.spawn_particles()

    def spawn_particles(self):
        self.particle_handler.add_particle(Particle(100, 100))
        self.particle_handler.add_particle(Particle(200, 100))
        self.particle_handler.add_particle(Particle(500, 100, xv=-5))
        self.particle_handler.add_particle(Particle(600, 100, xv=-5))
        self.particle_handler.add_particle(Particle(700, 100, xv=-5))
        # self.particle_handler.add_particle(Particle(100, 200))
        # self.particle_handler.add_particle(Particle(100, 400, yv=5))
        # for _ in range(1000):
        #     x = random.randint(50, WIDTH - 50)
        #     y = random.randint(50, HEIGHT - 50)
        #     radius = 3
        #     color = (0,255,255)#(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        #     xv = random.uniform(-2, 2)
        #     yv = 0#random.uniform(-2, 2)
        #     mass = radius * 0.1
        #     elasticity = 1
        #     particle = Particle(x, y, radius, color, xv, yv, mass, elasticity)
        #     self.particle_handler.add_particle(particle)

    def draw_text(self, text: str):
        y_offset = 5
        for line in text.split("\n"):
            text_surface = self.font.render(line, True, WHITE)
            self.screen.blit(text_surface, (10, y_offset))  # Draw text 10 pixels from the left
            y_offset += text_surface.get_rect().height + 5


    def main(self):
        while self.running:
            self.screen.fill(BLACK)

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # Update and draw particles
            self.particle_handler.apply_gravity()
            self.particle_handler.collide_all()
            self.particle_handler.update_particles()
            self.particle_handler.draw_particles(self.screen)
            self.draw_text(f"""Momentum     : {self.particle_handler.get_total_momentum():.2f}
KineticEnergy: {self.particle_handler.get_total_ke():.2f}
FPS          : {self.clock.get_fps():.0f}""")

            # Update the display
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

# Run the game
if __name__ == "__main__":
    game = Game()
    game.main()
