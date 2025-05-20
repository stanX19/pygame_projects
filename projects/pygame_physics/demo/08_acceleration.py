import pygame


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
    ball_x = 600
    ball_y = 350
    ball_xv = 1  # left
    ball_yv = 1  # down
    ball_color = (255, 255, 255)
    ball_radius = 50

    while Status.RUNNING:
        #Status.clock.tick(120)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                Status.RUNNING = False

        Status.window.fill((0, 0, 0))

        # move the ball
        # change ball's velocity
        if ball_x - ball_radius <= 0:  # leftmost radius hits left wall
            ball_xv = -ball_xv
        if ball_x + ball_radius >= Status.screen_size[0]:  # rightmost radius hits right wall
            ball_xv = -ball_xv
        if ball_y - ball_radius <= 0:  # topmost radius hits ceiling
            ball_yv = -ball_yv
        if ball_y + ball_radius >= Status.screen_size[1]:  # lower radius hits the floor
            ball_yv = -ball_yv

        # acceleration downwards
        ball_yv += 0.1  # increasing velocity downwards per unit [frame]

        # update ball's position
        ball_x += ball_xv
        ball_y += ball_yv

        # draw the ball
        pygame.draw.circle(Status.window, ball_color, (ball_x, ball_y), ball_radius)

        pygame.display.update()
    pygame.quit()


if __name__ == '__main__':
    run()