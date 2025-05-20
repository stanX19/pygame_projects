import pygame
import math


class Ball:
    def __init__(self, x, y, xv, yv, color, mass, radius):
        self.x = x
        self.y = y
        self.xv = xv
        self.yv = yv
        self.color = color
        self.mass = mass
        self.rad = radius

    def update(self):
        # change x
        self.x += self.xv

        # bounce x
        if self.x + self.rad > Status.screen_size[0]:
            self.xv = -self.xv
            self.x = 2 * Status.screen_size[0] - self.x - 2 * self.rad  # reflects x position

        elif self.x - self.rad < 0:
            self.xv = -self.xv
            self.x = -self.x + 2 * self.rad  # reflects x position

        # change y
        self.y += self.yv

        # bounce y
        if self.y + self.rad > Status.screen_size[1]:
            self.yv = -self.yv
            self.y = 2 * Status.screen_size[1] - self.y - 2 * self.rad  # reflects y position
        elif self.y - self.rad < 0:
            self.yv = -self.yv
            self.y = -self.y + 2 * self.rad  # reflects y position

    def collide(self, other):
        # just accept, dont ask
        y_dis = self.y - other.y
        x_dis = self.x - other.x
        dis = math.sqrt((x_dis) ** 2 + (y_dis) ** 2)

        if dis == 0: # perfectly overlaps
            self.x += 1
            self.y += 1
            y_dis = 1
            x_dis = 1
            dis = math.sqrt(2)

        y_over_dis = y_dis / dis
        x_over_dis = x_dis / dis

        self_tan = (self.yv * -x_over_dis + self.xv * y_over_dis)
        self_norm = (self.yv * y_over_dis + self.xv * x_over_dis)

        other_tan = (other.yv * -x_over_dis + other.xv * y_over_dis)
        other_norm = (other.yv * y_over_dis + other.xv * x_over_dis)

        # formula src: https://www.vobarian.com/collisions/2dcollisions2.pdf
        self_final_norm = (self_norm * (self.mass - other.mass) + 2 * other.mass * other_norm) \
                          / (self.mass + other.mass)
        obj_final_norm = (other_norm * (other.mass - self.mass) + 2 * self.mass * self_norm) \
                         / (other.mass + self.mass)

        self.xv = self_tan * y_over_dis + self_final_norm * x_over_dis
        self.yv = self_tan * -x_over_dis + self_final_norm * y_over_dis

        other.xv = other_tan * y_over_dis + obj_final_norm * x_over_dis
        other.yv = other_tan * -x_over_dis + obj_final_norm * y_over_dis


class Color:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)


class Status:
    screen_size = (1200, 700)
    window = pygame.display.set_mode(screen_size)  # to access our Status.window
    clock = pygame.time.Clock()  # manages fps
    RUNNING = True


def run():
    pygame.init()
    pygame.display.set_caption("the best game ever")  # title

    # ball data
    balls = [
        Ball(600, 350, -1, 0, (255, 255, 255), 100, 50),
        Ball(700, 350, 0, 1, (255, 255, 100), 100, 50),
        Ball(800, 350, 0, -1, (255, 100, 100), 100, 50),
        Ball(900, 350, 1, 0, (100, 255, 100), 100, 50),
    ]

    for i in range(100):
        balls.append(Ball(i * 10, 350, 1, 0, (100, 255, 100), 100, 10),)

    while Status.RUNNING:
        Status.clock.tick(120)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                Status.RUNNING = False

        Status.window.fill((0, 0, 0))

        for idx, ball in enumerate(balls):
            # detect collision with other ball
            for other in balls[idx + 1:]:
                rad = ball.rad + other.rad
                if math.sqrt((ball.x - other.x) ** 2 + (ball.y - other.y) ** 2) < rad:
                    ball.collide(other)

            # move the ball
            ball.update()

            # draw the ball
            pygame.draw.circle(Status.window, ball.color, (ball.x, ball.y), ball.rad)

        pygame.display.update()
    pygame.quit()


if __name__ == '__main__':
    run()