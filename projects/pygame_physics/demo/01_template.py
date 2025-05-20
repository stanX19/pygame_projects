import pygame


def run():
    pygame.init()
    pygame.display.set_caption("the best game ever")  # title
    clock = pygame.time.Clock()  # manages fps
    screen_size = (1200, 700)
    window = pygame.display.set_mode(screen_size)  # to access our window
    RUNNING = True

    while RUNNING:
        clock.tick(60)  # set fps

        window.fill((0, 0, 0))  # background color

        pygame.draw.circle(window, (255, 255, 255), (500, 500), 10)
        #              The window; color;           coordinate; radius

        pygame.display.update()  # updates the screen
    pygame.quit()


if __name__ == '__main__':
    run()
