import pygame


class Ball:
    def __init__(self, x, y, xv, yv, color, radius):
        self.x = x
        self.y = y
        self.xv = xv
        self.yv = yv
        self.color = color
        self.rad = radius

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
        # change ball's velocity
        if ball_1.x - ball_1.rad <= 0:  # leftmost radius hits left wall
            ball_1.xv = -ball_1.xv
        if ball_1.x + ball_1.rad > Status.screen_size[0]:  # rightmost radius hits right wall
            ball_1.xv = -ball_1.xv
        if ball_1.y - ball_1.rad <= 0:  # topmost radius hits ceiling
            ball_1.yv = -ball_1.yv
        if ball_1.y + ball_1.rad > Status.screen_size[1]:  # lower radius hits the floor
            ball_1.yv = -ball_1.yv
        
        # update ball's position
        ball_1.x += ball_1.xv
        ball_1.y += ball_1.yv

        # draw the ball
        pygame.draw.circle(Status.window, ball_1.color, (ball_1.x, ball_1.y), ball_1.rad)

        pygame.display.update()
    pygame.quit()


if __name__ == '__main__':
    run()
