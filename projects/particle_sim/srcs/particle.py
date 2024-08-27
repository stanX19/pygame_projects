import math

import pygame


class Particle:
    def __init__(self, x: float, y: float, radius: float = 50, color: tuple[int, int, int] = (255, 255, 255),
                 xv: float = 0, yv: float = 0, mass: float = 10.0, elasticity: float = 1.0):
        self.x: float = x
        self.y: float = y
        self.rad: float = radius
        self.color: tuple[int, int, int] = color
        self.xv: float = xv
        self.yv: float = yv
        self.mass: float = mass
        self.elasticity: float = elasticity

    @property
    def momentum(self) -> tuple[float, float]:
        return self.mass * self.xv, self.mass * self.yv

    @property
    def kinetic_energy(self) -> float:
        return self.mass * self.speed ** 2 / 2

    @property
    def speed(self) -> float:
        return math.hypot(self.xv, self.yv)

    def overlaps_with(self, other: 'Particle'):
        return math.hypot(self.x - other.x, self.y - other.y) <= self.rad + other.rad

    def move(self):
        self.x += self.xv
        self.y += self.yv

    def wall_bound(self, width: float, height: float) -> bool:
        hit_wall = False

        if self.x + self.rad > width and self.xv > 0:
            self.xv = -self.xv
            hit_wall = True
            self.x -= self.x + self.rad - width
        elif self.x - self.rad < 0 and self.xv < 0:
            self.xv = -self.xv
            hit_wall = True
            self.x += - (self.x - self.rad)
        if self.y + self.rad > height and self.yv > 0:
            self.yv = -self.yv
            hit_wall = True
            self.y -= self.y + self.rad - height
        elif self.y - self.rad < 0 and self.yv < 0:
            self.yv = -self.yv
            hit_wall = True
            self.y += - (self.y - self.rad)

        return hit_wall

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.rad)
