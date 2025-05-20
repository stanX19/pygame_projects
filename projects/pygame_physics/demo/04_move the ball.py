import pygame


def run():
    pygame.init()
    pygame.display.set_caption("the best game ever")  # title
    clock = pygame.time.Clock()  # manages fps
    screen_size = (1200, 700)
    window = pygame.display.set_mode(screen_size)  # to access our window
    RUNNING = True

    # ball data
    ball_x = 600
    ball_y = 350
    ball_xv = 1
    ball_yv = 1
    ball_color = (255, 255, 255)
    ball_radius = 50

    while RUNNING:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                RUNNING = False

        window.fill((0, 0, 0))

        # move the ball
        ball_x += ball_xv
        ball_y += ball_yv

        # draw the ball
        pygame.draw.circle(window, ball_color, (ball_x, ball_y), ball_radius)

        pygame.display.update()
    pygame.quit()


if __name__ == '__main__':
    run()