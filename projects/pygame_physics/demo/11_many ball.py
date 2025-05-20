import pygame


class Ball:
    def __init__(self, x, y, xv, yv, color, radius):
        self.x = x
        self.y = y
        self.xv = xv
        self.yv = yv
        self.color = color
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
        Ball(600, 350, 10, 1, (255, 255, 255), 50),
        Ball(700, 350, 1, 1, (255, 255, 100), 50),
        Ball(800, 350, 1, 1, (255, 100, 100), 50),
        Ball(900, 350, 1, 1, (100, 255, 100), 50),
    ]

    while Status.RUNNING:
        Status.clock.tick(120)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                Status.RUNNING = False

        Status.window.fill((0, 0, 0))

        for ball in balls:
            # move the ball
            ball.update()

            # draw the ball
            pygame.draw.circle(Status.window, ball.color, (ball.x, ball.y), ball.rad)

        pygame.display.update()
    pygame.quit()


if __name__ == '__main__':
    run()