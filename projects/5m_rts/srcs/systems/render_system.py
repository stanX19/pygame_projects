import pygame
import esper
import math
from srcs.config import *
from srcs.components import *

class RenderSystem(esper.Processor):
    def __init__(self, window, font):
        self.window = window
        self.font = font
    
    def _draw_upgrade_panel(self, sm):
        """Draw vertical upgrade panel at fixed position, hide when mouse moves away"""
        # Get upgrade system
        upgrade_sys = None
        for processor in self.world._processors:
            if processor.__class__.__name__ == 'UpgradeSystem':
                upgrade_sys = processor
                break
        
        if not upgrade_sys:
            return
        
        # Check what's selected
        selected_type = None
        selected_faction = None
        selected_entity = None
        has_selection = False
        
        # Check for selected entities
        for ent, (sel, ident) in self.world.get_components(Selectable, Identity):
            if sel.selected:
                has_selection = True
                selected_type = ident.type
                selected_faction = ident.faction
                selected_entity = ent
                break  # Only one entity can be selected at a time
        
        # Check for empty tile selection (if no entity is selected)
        if not has_selection and hasattr(sm, 'selected_empty_tile'):
            has_selection = True
            selected_type = 'empty_tile'
            selected_faction = None
            selected_entity = None
        
        # Clear empty tile marker if entity is selected
        if has_selection and selected_type != 'empty_tile' and hasattr(sm, 'selected_empty_tile'):
            delattr(sm, 'selected_empty_tile')
        
        # If nothing selected, don't show panel
        if not has_selection:
            # Clear saved position
            if hasattr(sm, 'upgrade_panel_position'):
                delattr(sm, 'upgrade_panel_position')
            return
            
        # Get mouse position
        mouse_pos = pygame.mouse.get_pos()
        
        # Panel sizing - vertical layout
        button_width = 180
        button_height = 35
        spacing_y = 38

        # Determine title and upgrades based on faction and type
        upgrade_defs = []
        panel_title = ""
        
        if selected_type == 'empty_tile':
             panel_title, upgrade_defs = upgrade_sys.get_empty_tile_options()
        elif selected_entity is not None:
             panel_title, upgrade_defs = upgrade_sys.get_entity_options(selected_entity)
        
        # Calculate panel dimensions (include title)
        title_height = 30
        panel_width = button_width + 20
        panel_height = title_height + len(upgrade_defs) * spacing_y + 15
        
        # Check if position was set by input system (when entity was selected)
        if not hasattr(sm, 'upgrade_panel_position'):
            # No position means panel was hidden - don't show it
            return
        
        # Use saved position (menu stays in place, doesn't follow mouse)
        panel_x, panel_y = sm.upgrade_panel_position
        
        # Check if mouse is hovering over the panel area
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        mouse_hovering = panel_rect.collidepoint(mouse_pos)
        
        # Only show if hovering OR within grace period
        # If hovering, keep the "last seen" time updated to now
        if mouse_hovering:
            sm.upgrade_panel_show_time = sm.game_time

        time_since_hover = sm.game_time - getattr(sm, 'upgrade_panel_show_time', 0.0)
        
        if not mouse_hovering and time_since_hover > 0.05:
            # Clear position when hiding
            if hasattr(sm, 'upgrade_panel_position'):
                delattr(sm, 'upgrade_panel_position')
            return
        
        # Panel background
        overlay = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        overlay.fill((10, 10, 20, 240))
        self.window.blit(overlay, panel_rect)
        pygame.draw.rect(self.window, (120, 120, 180), panel_rect, 2)
        
        # Title
        title_surf = pygame.font.SysFont("Arial", 14, bold=True).render(panel_title, True, (180, 180, 255))
        self.window.blit(title_surf, (panel_x + 10, panel_y + 8))
        
        # Get player faction info
        faction_id = sm.player_faction_id
        resources = sm.resources.get(faction_id, 0)
        upgrades = sm.faction_upgrades.get(faction_id, {})
        
        # Draw upgrade buttons vertically
        for i, (label, key, method_name, color) in enumerate(upgrade_defs):
            button_x = panel_x + 10
            button_y = panel_y + 30 + i * spacing_y
            # Button logic
            if key is None:
                # Action Button (no level, no cost)
                current_level = 0
                cost = 0
                main_text = label
                cost_text = ""
            else:
                # Upgrade Button
                current_level = upgrades.get(key, 0)
                
                # Use special cost function for range upgrades (5x more expensive)
                if key == 'unit_range':
                    cost = upgrade_sys.get_range_upgrade_cost(current_level)
                else:
                    cost = upgrade_sys.get_upgrade_cost(current_level)

                if current_level >= MAX_UPGRADE_LEVEL:
                    main_text = f"{label} [MAX]"
                    cost_text = ""
                else:
                    main_text = f"{label} Lv{current_level}"
                    cost_text = f"Cost: ${cost}"

            # Button rectangle
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            
            # Store button info for click detection
            if not hasattr(sm, 'upgrade_buttons'):
                sm.upgrade_buttons = []
            sm.upgrade_buttons.append((button_rect, method_name, key))
            
            # Check if mouse is over this button
            button_hover = button_rect.collidepoint(mouse_pos)
            
            # Button color based on affordability and hover
            if current_level >= MAX_UPGRADE_LEVEL and key is not None:
                btn_color = (40, 40, 40)
                text_color = (120, 120, 120)
            elif resources >= cost:
                if button_hover:
                    btn_color = (0, 150, 0)  # Brighter green on hover
                else:
                    btn_color = (0, 100, 0)
                text_color = (255, 255, 255)
            else:
                btn_color = (80, 40, 40)
                text_color = (160, 160, 160)
            
            # Draw button
            pygame.draw.rect(self.window, btn_color, button_rect)
            if button_hover and (current_level < MAX_UPGRADE_LEVEL or key is None):
                pygame.draw.rect(self.window, (255, 255, 255), button_rect, 2)
            else:
                pygame.draw.rect(self.window, color, button_rect, 2)
            
            # Main label
            text_surf = pygame.font.SysFont("Arial", 13, bold=True).render(main_text, True, text_color)
            self.window.blit(text_surf, (button_x + 8, button_y + 6))
            
            # Cost text (if not maxed)
            if cost_text:
                cost_color = (255, 215, 0) if resources >= cost else (150, 100, 100)
                cost_surf = pygame.font.SysFont("Arial", 11).render(cost_text, True, cost_color)
                self.window.blit(cost_surf, (button_x + 8, button_y + 20))

    def process(self):
        # Clear upgrade buttons from previous frame
        sm = self.world.scene_manager
        sm.upgrade_buttons = []
        
        self.window.fill(COLOR_BG)
        
        # Draw generated background if available
        if hasattr(sm, 'background_surface'):
            self.window.blit(sm.background_surface, (0, 0))

        # 2. Draw Entities
        # Sort by layer for correct depth
        # Note: In efficient ECS, we might cache this list
        render_list = []
        for ent, (trans, rend) in self.world.get_components(Transform, Renderable):
            render_list.append((ent, trans, rend))

        render_list.sort(key=lambda x: x[2].layer)

        for ent, trans, rend in render_list:
            color = rend.color

            # Highlight selected
            try:
                sel = self.world.component_for_entity(ent, Selectable)
                if sel.selected:
                    pygame.draw.circle(self.window, COLOR_SELECTION, (int(trans.x), int(trans.y)),
                                       int(trans.radius) + 2, 1)
            except KeyError:
                pass

            if rend.shape == 'circle':
                pygame.draw.circle(self.window, color, (int(trans.x), int(trans.y)), int(trans.radius))
            elif rend.shape == 'polygon' and rend.polygon_points:
                # Draw custom polygon for upgraded units
                translated_points = [(int(trans.x + px), int(trans.y + py)) for px, py in rend.polygon_points]
                if len(translated_points) >= 3:
                    pygame.draw.polygon(self.window, color, translated_points)
            elif rend.shape == 'hexagon':
                # Regular hexagon (for castles) with inner hexagon
                import math
                # Outer hexagon
                pts = []
                for i in range(6):
                    angle = math.pi / 3 * i - math.pi / 6  # Start from top
                    px = trans.x + trans.radius * math.cos(angle)
                    py = trans.y + trans.radius * math.sin(angle)
                    pts.append((int(px), int(py)))
                pygame.draw.polygon(self.window, color, pts)
                
                # Inner hexagon (smaller, brighter)
                inner_pts = []
                inner_radius = trans.radius * 0.6  # 60% of original size
                # Make brighter by adding to color components (capped at 255)
                brighter_color = tuple(min(255, int(c * 1.4)) for c in color)
                for i in range(6):
                    angle = math.pi / 3 * i - math.pi / 6
                    px = trans.x + inner_radius * math.cos(angle)
                    py = trans.y + inner_radius * math.sin(angle)
                    inner_pts.append((int(px), int(py)))
                pygame.draw.polygon(self.window, brighter_color, inner_pts)
            elif rend.shape == 'square':
                rect = pygame.Rect(trans.x - trans.radius, trans.y - trans.radius, trans.radius * 2, trans.radius * 2)
                pygame.draw.rect(self.window, color, rect)
            elif rend.shape == 'triangle':
                # Simple triangle math
                pts = [
                    (trans.x, trans.y - trans.radius),
                    (trans.x - trans.radius, trans.y + trans.radius),
                    (trans.x + trans.radius, trans.y + trans.radius)
                ]
                pygame.draw.polygon(self.window, color, pts)
            elif rend.shape == 'stacked_triangles':
                # Multiple overlapping triangles with varying darkness (for mountains)
                import math
                base_color = color
                # Draw 3 triangles with different sizes and darkness
                for i in range(3):
                    scale = 1.0 - (i * 0.15)  # Smaller triangles on top
                    darkness = 1.0 - (i * 0.3)  # Darker as we go back
                    triangle_color = tuple(int(c * darkness) for c in base_color)
                    offset_y = i * 4  # Offset each triangle down slightly
                    r = trans.radius * scale
                    pts = [
                        (trans.x, trans.y - r + offset_y),
                        (trans.x - r, trans.y + r + offset_y),
                        (trans.x + r, trans.y + r + offset_y)
                    ]
                    pygame.draw.polygon(self.window, triangle_color, pts)
            elif rend.shape == 'resource_grid':
                # Orange/faction-colored square with 3x3 yellow inner squares (for resource points)
                # Use the entity's color (changes when captured)
                outer_color = color  # Use dynamic color from entity
                
                # Outer square
                outer_rect = pygame.Rect(trans.x - trans.radius, trans.y - trans.radius, 
                                        trans.radius * 2, trans.radius * 2)
                pygame.draw.rect(self.window, outer_color, outer_rect)
                
                # 3x3 grid of smaller yellow squares with gaps
                grid_size = 3
                square_size = (trans.radius * 2 * 0.7) / grid_size  # 70% of outer size divided by 3
                gap = square_size * 0.2  # 20% gap
                actual_square = square_size - gap
                
                start_x = trans.x - (grid_size * square_size) / 2 + gap / 2
                start_y = trans.y - (grid_size * square_size) / 2 + gap / 2
                
                for row in range(grid_size):
                    for col in range(grid_size):
                        sx = start_x + col * square_size
                        sy = start_y + row * square_size
                        small_rect = pygame.Rect(sx, sy, actual_square, actual_square)
                        pygame.draw.rect(self.window, (255, 215, 0), small_rect)  # Yellow
            elif rend.shape == 'river_enhanced':
                # Enhanced river rendering - handled in separate pass below
                pass

            # Draw HP bar for damaged units
            try:
                stats = self.world.component_for_entity(ent, Stats)
                if stats.hp < stats.max_hp:
                    bar_w = trans.radius * 2
                    ratio = stats.hp / stats.max_hp
                    pygame.draw.rect(self.window, (50, 0, 0),
                                     (trans.x - trans.radius, trans.y - trans.radius - 5, bar_w, 4))
                    pygame.draw.rect(self.window, (0, 255, 0),
                                     (trans.x - trans.radius, trans.y - trans.radius - 5, bar_w * ratio, 4))
            except KeyError:
                pass

        # Second pass: Draw enhanced rivers with connections
        # Collect all river entities first
        river_entities = []
        river_positions = {}
        for ent, (trans, rend, ident) in self.world.get_components(Transform, Renderable, Identity):
            if rend.shape == 'river_enhanced' and ident.type == 'obstacle':
                river_entities.append((ent, trans, rend))
                # Store in grid coordinates for adjacency check
                grid_x = int(trans.x // TILE_SIZE)
                grid_y = int(trans.y // TILE_SIZE)
                river_positions[(grid_x, grid_y)] = (ent, trans, rend)
        
        # Draw rivers with connections
        for ent, trans, rend in river_entities:
            grid_x = int(trans.x // TILE_SIZE)
            grid_y = int(trans.y // TILE_SIZE)
            
            # Check for adjacent rivers in 4 cardinal directions
            adjacent = {
                'up': (grid_x, grid_y - 1) in river_positions,
                'down': (grid_x, grid_y + 1) in river_positions,
                'left': (grid_x - 1, grid_y) in river_positions,
                'right': (grid_x + 1, grid_y) in river_positions
            }
            
            water_color = rend.color  # Blue water
            
            # Draw base water circle
            pygame.draw.circle(self.window, water_color, (int(trans.x), int(trans.y)), int(trans.radius))
            
            # Draw connecting rectangles to adjacent rivers
            rect_width = trans.radius * 2
            
            if adjacent['up']:
                _, other_trans, _ = river_positions[(grid_x, grid_y - 1)]
                water_rect = pygame.Rect(trans.x - trans.radius, other_trans.y, rect_width, trans.y - other_trans.y)
                pygame.draw.rect(self.window, water_color, water_rect)
            
            if adjacent['down']:
                _, other_trans, _ = river_positions[(grid_x, grid_y + 1)]
                water_rect = pygame.Rect(trans.x - trans.radius, trans.y, rect_width, other_trans.y - trans.y)
                pygame.draw.rect(self.window, water_color, water_rect)
            
            if adjacent['left']:
                _, other_trans, _ = river_positions[(grid_x - 1, grid_y)]
                water_rect = pygame.Rect(other_trans.x, trans.y - trans.radius, trans.x - other_trans.x, rect_width)
                pygame.draw.rect(self.window, water_color, water_rect)
            
            if adjacent['right']:
                _, other_trans, _ = river_positions[(grid_x + 1, grid_y)]
                water_rect = pygame.Rect(trans.x, trans.y - trans.radius, other_trans.x - trans.x, rect_width)
                pygame.draw.rect(self.window, water_color, water_rect)

        # Draw Construction Progress (Overlay on sites)
        for ent, (trans, site) in self.world.get_components(Transform, ConstructionSite):
            # Draw bar above site
            prog = min(1.0, site.elapsed / site.total_time)
            bar_w = trans.radius * 2
            bar_h = 6
            bg_rect = pygame.Rect(trans.x - trans.radius, trans.y - trans.radius - 10, bar_w, bar_h)
            fill_rect = pygame.Rect(trans.x - trans.radius, trans.y - trans.radius - 10, bar_w * prog, bar_h)
            
            pygame.draw.rect(self.window, (50, 50, 50), bg_rect)
            pygame.draw.rect(self.window, (0, 255, 255), fill_rect) # Cyan for construction

        # 3. Draw UI
        sm = self.world.scene_manager

        # Drag Selection Box
        input_sys = None
        for sys in self.world._processors:
            if sys.__class__.__name__ == 'InputSystem':
                input_sys = sys
                break

        if input_sys and input_sys.selecting:
            rect = pygame.Rect(input_sys.drag_start, (
            input_sys.drag_current[0] - input_sys.drag_start[0], input_sys.drag_current[1] - input_sys.drag_start[1]))
            rect.normalize()
            pygame.draw.rect(self.window, COLOR_SELECTION, rect, 1)

        # Circular Progress Bar for Hold Action (Build or Select)
        if input_sys and input_sys.is_holding and input_sys.hold_timer > 0.1:
            prog = min(1.0, input_sys.hold_timer / 0.4) # 0.4s threshold
            center = input_sys.drag_current
            radius = 20
            
            # Draw bg
            pygame.draw.circle(self.window, (100, 100, 100), center, radius, 2)
            
            # Draw arc
            rect = pygame.Rect(center[0] - radius, center[1] - radius, radius * 2, radius * 2)
            angle = 360 * prog
            pygame.draw.arc(self.window, (0, 255, 255), rect, math.radians(-90), math.radians(-90 + angle), 4)             

        # HUD
        timer_text = f"Time: {int(sm.game_time // 60)}:{int(sm.game_time % 60):02d}"
        res_text = f"Resources: {int(sm.resources[sm.player_faction_id])}"
        sd_text = "SUDDEN DEATH!" if sm.sudden_death else ""

        surf_time = self.font.render(timer_text, True, COLOR_TEXT)
        surf_res = self.font.render(res_text, True, COLOR_RESOURCE)
        surf_sd = self.font.render(sd_text, True, (255, 50, 50))

        self.window.blit(surf_time, (10, 10))
        self.window.blit(surf_res, (10, 40))
        self.window.blit(surf_sd, (SCREEN_WIDTH // 2 - 100, 10))
        
        # Draw Upgrade Panel
        self._draw_upgrade_panel(sm)

        # Draw Flash Message
        if sm.message_timer > 0:
            sm.message_timer -= sm.dt
            msg_surf = self.font.render(sm.message, True, sm.message_color)
            msg_rect = msg_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            
            # Background
            bg_rect = msg_rect.inflate(20, 10)
            overlay = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.window.blit(overlay, bg_rect)
            self.window.blit(msg_surf, msg_rect)

        # Draw Floating Messages
        for msg in sm.floating_messages[:]:
            text, x, y, timer, color = msg
            msg[3] -= sm.dt  # Decrement timer
            
            if msg[3] <= 0:
                sm.floating_messages.remove(msg)
                continue
                
            y_pos = y - (1.0 - msg[3]) * 30  # Float up
            
            surf = self.font.render(text, True, color)
            # Alpha fading manually (blit with special flags or just color fade if simple)
            # Simple approach: Don't fade alpha, just remove. Or use special blit.
            # Pygame font render doesn't support alpha directly on surface without set_alpha?
            # It does.
            surf.set_alpha(int(msg[3] * 255))
            self.window.blit(surf, (x, int(y_pos)))

        # Game Over Screen
        if sm.game_over:
            # Semi-transparent dark overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            self.window.blit(overlay, (0, 0))
            
            # Large game over text
            big_font = pygame.font.SysFont("Arial", 72, bold=True)
            medium_font = pygame.font.SysFont("Arial", 48, bold=True)

            
            # Winner text
            if sm.winner:
                # Determine winner display text
                if sm.winner == sm.player_faction_id:
                    winner_text = "VICTORY"
                    winner_color = sm.get_faction_color(sm.winner)
                else:
                    winner_text = "DEFEAT"
                    winner_color = sm.get_faction_color(sm.winner)
                surf_winner = medium_font.render(winner_text, True, winner_color)
                winner_rect = surf_winner.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
                self.window.blit(surf_winner, winner_rect)
            else:
                # Draw
                draw_text = "DRAW"
                surf_draw = medium_font.render(draw_text, True, (200, 200, 200))
                draw_rect = surf_draw.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
                self.window.blit(surf_draw, draw_rect)

        pygame.display.flip()