import pygame


def run():
    pygame.init()
    pygame.display.set_caption("the best game ever")  # title
    clock = pygame.time.Clock()  # manages fps
    screen_size = (1200, 700)
    window = pygame.display.set_mode(screen_size)  # to access our window
    RUNNING = True

    while RUNNING:
        clock.tick(60)

        # there can be many event
        # we will loop through it to seek for the one we are want to response to
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # cross button
                RUNNING = False  # while loop will stop if this is FALSE

        window.fill((0, 0, 0))
        pygame.draw.circle(window, (255, 255, 255), (500, 500), 10)
        pygame.display.update()
    pygame.quit()


if __name__ == '__main__':
    run()