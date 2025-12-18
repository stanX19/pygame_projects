
import pygame
try:
    pygame.init()
    info = pygame.display.Info()
    print(f"Current W: {info.current_w}, H: {info.current_h}")
    try:
        print(f"Get Screen Size: {pygame.display.get_screen_size()}")
    except AttributeError:
        print("pygame.display.get_screen_size() does not exist")
except Exception as e:
    print(f"Error: {e}")
