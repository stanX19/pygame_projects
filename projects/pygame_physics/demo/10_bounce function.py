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
    ball_1 = Ball(600, 350, 1, 1, (255, 255, 255), 50)

    while Status.RUNNING:
        Status.clock.tick(120)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                Status.RUNNING = False

        Status.window.fill((0, 0, 0))

        # move the ball
        ball_1.update()

        # draw the ball
        pygame.draw.circle(Status.window, ball_1.color, (ball_1.x, ball_1.y), ball_1.rad)

        pygame.display.update()
    pygame.quit()


if __name__ == '__main__':
    run()
