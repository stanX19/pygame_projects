import pygame
import keyboard


class Color:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)


class Status:
    screen_size = (1200, 700)
    window = pygame.display.set_mode(screen_size)  # to access our Status.window
    clock = pygame.time.Clock()  # manages fps
    RUNNING = True


def vertical_ke(ball_yv, ball_mass=1000):
    return ball_mass * (ball_yv ** 2) / 2


def gpe(ball_y, gravitational_acceleration, ball_mass=1000):
    return ball_mass * gravitational_acceleration * ball_y


def run():
    pygame.init()
    pygame.display.set_caption("the best game ever")  # title

    # font
    consolas = pygame.font.SysFont("consolas", 24, bold=True, italic=False)

    # ball data
    ball_x = 600
    ball_y = 350
    ball_xv = 1  # left
    ball_yv = 1  # down
    ball_color = (255, 255, 255)
    ball_radius = 50

    # env data
    gravitational_acceleration = 0.1  # per frame

    while Status.RUNNING:
        Status.clock.tick(120)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                Status.RUNNING = False

        Status.window.fill((0, 0, 0))

        # slow the program down
        # reads the keyboard using pygame module, if shift is not pressed, continue instead of simulating
        # Q: why don't use input()
        # A: this will make the entire pygame page unresponsive
        if not keyboard.is_pressed("enter"):
            continue

        # print out the data
        KE_Y = round(vertical_ke(ball_yv))
        y_from_bottom = Status.screen_size[1] - ball_y - ball_radius
        GPE = round(gpe(y_from_bottom, gravitational_acceleration))

        Status.window.blit(consolas.render(f"KE(v): {KE_Y:>8} {'█' * (KE_Y // 500)}", True, (255, 255, 255)), (10, 10))
        Status.window.blit(consolas.render(f"  GPE: {GPE:>8} {'█' * (GPE // 500)}", True, (255, 255, 255)), (10, 40))
        Status.window.blit(consolas.render(f"total: {KE_Y + GPE:>8} {'█' * ((KE_Y + GPE) // 500)}", True, (255, 255, 255)), (10, 70))
        print(f"KE: {KE_Y}, GPE: {GPE}, total: {KE_Y + GPE}")

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
        ball_yv += gravitational_acceleration / 2  # because of the nature of v-t graph, must take half

        # update ball's position
        ball_x += ball_xv
        ball_y += ball_yv

        ball_yv += gravitational_acceleration / 2

        # draw the ball
        pygame.draw.circle(Status.window, ball_color, (ball_x, ball_y), ball_radius)

        pygame.display.update()
    pygame.quit()


if __name__ == '__main__':
    run()
