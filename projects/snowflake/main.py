import math
import sys
from collections import deque

import pygame

# Initialize Pygame
pygame.init()

# Constants
CANVAS_HEIGHT = 300
CANVAS_WIDTH = int(CANVAS_HEIGHT * math.tan(math.pi / 6))
PADDING = 50
DISPLAY_HEIGHT = CANVAS_HEIGHT * 2
DISPLAY_WIDTH = DISPLAY_HEIGHT / math.cos(math.pi / 6)

LEFT_CANVAS_RECT = pygame.Rect(PADDING, PADDING, CANVAS_WIDTH, CANVAS_HEIGHT)
RIGHT_CANVAS_RECT = pygame.Rect(CANVAS_WIDTH + 2 * PADDING, PADDING, DISPLAY_WIDTH, DISPLAY_HEIGHT)

SCREEN_WIDTH, SCREEN_HEIGHT = RIGHT_CANVAS_RECT.right + PADDING, RIGHT_CANVAS_RECT.bottom + PADDING

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)

BRUSH_RADIUS = 5
UNDO_LIMIT = 50


class PaintApp:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.display.set_caption("Snowflake Generator")

        # Drawing surfaces for the two canvases
        self.left_canvas = pygame.Surface((LEFT_CANVAS_RECT.width, LEFT_CANVAS_RECT.height), pygame.SRCALPHA)
        self.right_canvas = pygame.Surface((RIGHT_CANVAS_RECT.width, RIGHT_CANVAS_RECT.height), pygame.SRCALPHA)

        self.left_canvas.fill((0, 0, 0, 0))  # Initialize the left canvas as transparent
        self.right_canvas.fill((128, 128, 128))  # Initialize the right canvas as black

        # Undo stack
        self.undo_stack = deque(maxlen=UNDO_LIMIT)

        # Drawing state
        self.drawing = False
        self.eraser = False
        self.last_pos = None

        # Fill screen button
        self.fill_button = pygame.Rect(50, 10, 150, 30)
        self.fill_with_black = False


    def draw_rounded_line(self, color, start_pos, end_pos, radius):
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        dist = max(abs(dx), abs(dy))

        if dist > 0:
            for i in range(dist):
                x = int(start_pos[0] + float(i) / dist * dx)
                y = int(start_pos[1] + float(i) / dist * dy)
                if not self.is_in_triangle((x, y)):
                    continue
                pygame.draw.circle(self.left_canvas, color, (x, y), radius)

        # Draw end caps as circles
        if self.is_in_triangle(start_pos):
            pygame.draw.circle(self.left_canvas, color, start_pos, radius)
        if self.is_in_triangle(end_pos):
            pygame.draw.circle(self.left_canvas, color, end_pos, radius)

    def save_state(self):
        self.undo_stack.append(self.left_canvas.copy())

    def undo(self):
        if self.undo_stack:
            previous_state = self.undo_stack.pop()
            self.left_canvas = previous_state
            self.update_right_canvas()

    def toggle_fill(self):
        # Fill the left canvas with transparency or black
        self.save_state()
        self.left_canvas.fill((0, 0, 0, 0))
        if not self.fill_with_black:
            pygame.draw.polygon(self.left_canvas, (255, 255, 255, 255),
                                ((0, 0), (CANVAS_WIDTH, 0), (CANVAS_WIDTH, CANVAS_HEIGHT)))
        self.update_right_canvas()
        self.eraser = not self.fill_with_black
        self.fill_with_black = not self.fill_with_black

    def update_right_canvas(self):
        self.right_canvas.fill((128, 128, 128))  # Fill with transparent black

        canvas = pygame.Surface((CANVAS_WIDTH * 2, CANVAS_HEIGHT * 2), pygame.SRCALPHA)  # Allow transparency
        canvas.blit(self.left_canvas, (0, 0))
        canvas.blit(pygame.transform.flip(self.left_canvas, True, False), (CANVAS_WIDTH, 0))
        hex_center = (RIGHT_CANVAS_RECT.width // 2, RIGHT_CANVAS_RECT.height // 2)

        for i in range(6):
            angle = i * math.pi / 3
            rotated_surface = pygame.transform.rotate(canvas, math.degrees(angle))
            rotated_rect = rotated_surface.get_rect()
            rotated_rect.center = hex_center
            self.right_canvas.blit(rotated_surface, rotated_rect.topleft)

    def is_in_triangle(self, pos):
        # Check if a point is within the drawing triangle
        x, y = pos
        if x < 0 or x > CANVAS_WIDTH or y < 0 or y > CANVAS_HEIGHT:
            return False

        # Equilateral triangle vertices
        p1 = (0, 0)
        p2 = (CANVAS_WIDTH, 0)
        p3 = (CANVAS_WIDTH, CANVAS_HEIGHT)

        # Barycentric method to determine if a point is inside the triangle
        denominator = (p2[1] - p3[1]) * (p1[0] - p3[0]) + (p3[0] - p2[0]) * (p1[1] - p3[1])
        a = ((p2[1] - p3[1]) * (x - p3[0]) + (p3[0] - p2[0]) * (y - p3[1])) / denominator
        b = ((p3[1] - p1[1]) * (x - p3[0]) + (p1[0] - p3[0]) * (y - p3[1])) / denominator
        c = 1 - a - b

        return 0 <= a <= 1 and 0 <= b <= 1 and 0 <= c <= 1

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.fill_button.collidepoint(event.pos):
                    self.toggle_fill()
                else:
                    self.drawing = True
                    self.last_pos = (event.pos[0] - LEFT_CANVAS_RECT.x, event.pos[1] - LEFT_CANVAS_RECT.y)
                    self.save_state()

            if event.type == pygame.MOUSEBUTTONUP:
                self.drawing = False
                self.last_pos = None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    self.undo()
                if event.key == pygame.K_e:
                    self.eraser = not self.eraser

    def draw_interface(self):
        # Fill the background
        self.screen.fill(GRAY)

        # Draw the fill button
        fill_text = "Fill with Black" if self.fill_with_black else "Fill with White"
        pygame.draw.rect(self.screen, BLACK, self.fill_button)
        font = pygame.font.Font(None, 24)
        text_surface = font.render(fill_text, True, WHITE)
        self.screen.blit(text_surface, (self.fill_button.x + 10, self.fill_button.y + 5))

        # Draw the left canvas triangle border
        pygame.draw.polygon(self.screen, WHITE, [
            (LEFT_CANVAS_RECT.x, LEFT_CANVAS_RECT.y),
            (LEFT_CANVAS_RECT.x + CANVAS_WIDTH, LEFT_CANVAS_RECT.y + CANVAS_HEIGHT),
            (LEFT_CANVAS_RECT.x + CANVAS_WIDTH, LEFT_CANVAS_RECT.y)
        ], 1)

        # Draw the right canvas border
        pygame.draw.rect(self.screen, BLACK, RIGHT_CANVAS_RECT)
        self.screen.blit(self.left_canvas, (LEFT_CANVAS_RECT.x, LEFT_CANVAS_RECT.y))
        self.screen.blit(self.right_canvas, (RIGHT_CANVAS_RECT.x, RIGHT_CANVAS_RECT.y))

        # Display tool information
        tool_text = "Eraser ON" if self.eraser else "Eraser OFF"
        brush_info = f"Brush: {BRUSH_RADIUS}px | {tool_text} (Press 'E' to toggle)"
        info_surface = font.render(brush_info, True, WHITE)
        self.screen.blit(info_surface, (250, 10))

    def do_mouse_draw(self):
        if not self.drawing:  # or not LEFT_CANVAS_RECT.collidepoint(pygame.mouse.get_pos()):
            return
        mouse_x, mouse_y = pygame.mouse.get_pos()
        canvas_x = mouse_x - LEFT_CANVAS_RECT.x
        canvas_y = mouse_y - LEFT_CANVAS_RECT.y

        if self.last_pos:
            if self.eraser:
                self.draw_rounded_line((0, 0, 0, 0), self.last_pos, (canvas_x, canvas_y), BRUSH_RADIUS)
            else:
                self.draw_rounded_line(WHITE, self.last_pos, (canvas_x, canvas_y), BRUSH_RADIUS)

            self.update_right_canvas()

        self.last_pos = (canvas_x, canvas_y)

    def run(self):
        clock = pygame.time.Clock()
        while True:
            self.handle_events()
            self.do_mouse_draw()
            self.draw_interface()
            pygame.display.flip()
            clock.tick(60)


if __name__ == "__main__":
    PaintApp().run()
