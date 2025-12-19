import pygame
import esper
import math
from config import *
from components import *

# Selection Bitmasks
SELECT_NONE = 0
SELECT_CLICK = 1
SELECT_DRAG = 2
SELECT_HOLD = 4

class InputSystem(esper.Processor):
    def __init__(self, scene_manager):
        self.scene_manager = scene_manager
        self.selecting = False
        self.drag_start = (0, 0)
        self.drag_current = (0, 0)
        
        # Unified Interaction State
        self.hold_timer = 0.0
        self.is_holding = False
        self.holding_complete = False
        self.interaction_target = None
        self.start_pos = (0, 0)
        self.hold_threshold = 0.4 # Seconds for hold action

    def process(self):
        dt = self.scene_manager.dt
        mouse_pos = pygame.mouse.get_pos()
        
        # Handle Mouse Events
        self._handle_mouse_input(dt, mouse_pos)
        
        # Update Hold Logic
        if self.is_holding and not self.holding_complete:
            self.hold_timer += dt
            if self.hold_timer > self.hold_threshold:
                self._trigger_hold_action()
                self.holding_complete = True
        elif not self.is_holding:
            self.hold_timer = 0.0

    def _handle_mouse_input(self, dt, mouse_pos):
        events = self.scene_manager.events
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left Click
                    if self._check_upgrade_buttons(mouse_pos):
                        continue
                    self._handle_left_click(mouse_pos)

                elif event.button == 3: # Right Click
                     self._handle_right_click(mouse_pos)

            elif event.type == pygame.MOUSEMOTION:
                self.drag_current = mouse_pos
                
                # Check for Drag Threshold to cancel Hold
                if self.is_holding:
                    dist_sq = (mouse_pos[0] - self.start_pos[0])**2 + (mouse_pos[1] - self.start_pos[1])**2
                    if dist_sq > 100: # Drag threshold 10px
                        self.is_holding = False # Cancel hold
                        self.selecting = True   # Start drag selection
                        self.hold_timer = 0.0
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self._handle_left_release()

    def _handle_left_click(self, mouse_pos):
        self.start_pos = mouse_pos
        self.drag_start = mouse_pos
        self.drag_current = mouse_pos
        
        # Identify potential target
        self.interaction_target = self._get_entity_at(mouse_pos)
        
        # Start Holding State
        self.is_holding = True
        self.holding_complete = False
        self.hold_timer = 0.0
        self.selecting = False # Don't select yet, wait to see if it's a hold

    def _handle_left_release(self):
        # If we were holding and didn't complete hold action -> Tap
        if self.is_holding and not self.holding_complete:
            if self.interaction_target:
                self._trigger_tap_action(self.interaction_target)
            else:
                # Tap on empty space -> Deselect all
                for ent, sel in self.world.get_component(Selectable):
                    sel.selected = False

        # Cleanup
        self.is_holding = False
        self.holding_complete = False
        self.hold_timer = 0.0
        self.interaction_target = None
        
        if self.selecting:
            self._finish_selection()
            self.selecting = False

    def _trigger_hold_action(self):
        # 1. If Target supports HOLD -> Select IT
        handled_hold_select = False
        if self.interaction_target:
            mask = 0
            if self.world.has_component(self.interaction_target, Selectable):
                mask = self.world.component_for_entity(self.interaction_target, Selectable).selection_mask
                
            if mask & SELECT_HOLD:
                self._select_single(self.interaction_target)
                handled_hold_select = True
        
        # 2. If No Target OR Target doesn't support HOLD -> Try Build Castle
        if not handled_hold_select:
            self._start_construction()

    def _trigger_tap_action(self, ent):
        ident = self.world.component_for_entity(ent, Identity)
        
        # Castle Tap -> Spawn Unit (only if owned by player)
        if ident.type == 'castle':
            player_faction = self.scene_manager.player_faction_id
            if ident.faction == player_faction:
                trans = self.world.component_for_entity(ent, Transform)
                self._spawn_unit_burst(trans.x, trans.y)
        
        # Other Entity Tap -> Select
        else:
            if self.world.has_component(ent, Selectable):
                 mask = self.world.component_for_entity(ent, Selectable).selection_mask
                 if mask & SELECT_CLICK:
                     self._select_single(ent)

    def _start_construction(self):
        # 1. Determine Build Site (Snap to Tile)
        mx, my = self.drag_current
        
        # Snap to grid
        grid_x = int(mx // TILE_SIZE)
        grid_y = int(my // TILE_SIZE)
        
        # Clamp to map bounds
        grid_x = max(0, min(grid_x, MAP_COLS - 1))
        grid_y = max(0, min(grid_y, MAP_ROWS - 1))
        
        # Calculate world center of that tile
        center_x = grid_x * TILE_SIZE + TILE_SIZE / 2
        center_y = grid_y * TILE_SIZE + TILE_SIZE / 2

        # 2. Check Overlap - Only check if target tile is occupied
        for ent, (trans, ident) in self.world.get_components(Transform, Identity):
            if ident.type in ['castle', 'resource', 'obstacle']:
                dist = math.hypot(trans.x - center_x, trans.y - center_y)
                if dist < 20: 
                    # If it's an ally castle, select it instead of error
                    if ident.type == 'castle' and ident.faction == self.scene_manager.player_faction_id:
                         self._select_single(ent)
                         return

                    self.scene_manager.show_message("Cannot build: Tile Occupied!", (255, 50, 50))
                    return

        # 3. Check Unit Count
        selected_units = [] # List of (entity, transform)
        for ent, (trans, sel) in self.world.get_components(Transform, Selectable):
            if sel.selected:
                selected_units.append((ent, trans))
        
        if len(selected_units) < CASTLE_BUILD_REQ:
            self.scene_manager.show_message(f"Need {CASTLE_BUILD_REQ} units!", (255, 50, 50))
            return

        # 4. Check Cost & Start Construction
        player_id = self.scene_manager.player_faction_id
        if self.scene_manager.resources[player_id] >= CASTLE_BUILD_COST:
            self.scene_manager.resources[player_id] -= CASTLE_BUILD_COST
            
            units_to_sacrifice = selected_units[:CASTLE_BUILD_REQ]
            
            # Create Construction Site
            self.world.create_entity(
                Transform(x=center_x, y=center_y, radius=CASTLE_RADIUS),
                ConstructionSite(total_time=CASTLE_CONSTRUCTION_TIME, elapsed=0.0, 
                                 units_ids=[u[0] for u in units_to_sacrifice], faction=player_id),
                Renderable(color=(100, 100, 100), shape='square', layer=0) # Grey placeholder
            )
            
            # Command units to move to site
            for unit_ent, _ in units_to_sacrifice:
                # Deselect
                try:
                    self.world.component_for_entity(unit_ent, Selectable).selected = False
                except KeyError: pass
                
                # Move to center
                try:
                    mov = self.world.component_for_entity(unit_ent, Movement)
                    mov.target_x = center_x
                    mov.target_y = center_y
                    mov.moving = True
                except KeyError: pass

            print("Construction Started!")
        else:
            self.scene_manager.show_message("Not enough Resources!", (255, 50, 50))

    def _check_upgrade_buttons(self, mouse_pos):
        """Check if player clicked on an upgrade button. Returns True if clicked."""
        # Get stored button rectangles from scene manager (set during rendering)
        if not hasattr(self.scene_manager, 'upgrade_buttons'):
            return False
        
        # Get upgrade system
        upgrade_sys = None
        for processor in self.world._processors:
            if processor.__class__.__name__ == 'UpgradeSystem':
                upgrade_sys = processor
                break
        
        if not upgrade_sys:
            return False
        
        faction_id = self.scene_manager.player_faction_id
        
        # Check each button
        for button_rect, method_name, upgrade_key in self.scene_manager.upgrade_buttons:
            if button_rect.collidepoint(mouse_pos):
                
                # Handle special "Spawn Unit" button
                if method_name == 'spawn_unit':
                     self.scene_manager.spawn_unit(0, 0) # Coords don't matter? Wait, they do.
                     # Original spawn unit needed coords to offset.
                     # But UI button doesn't have coords.
                     # Let's find the selected castle!
                     
                     for ent, (sel, trans, ident) in self.world.get_components(Selectable, Transform, Identity):
                         if sel.selected and ident.type == 'castle' and ident.faction == faction_id:
                             self.scene_manager.spawn_unit(trans.x, trans.y)
                             break
                     return True

                # Try to purchase upgrade
                method = getattr(upgrade_sys, method_name)
                success = method(faction_id)
                
                if success:
                    label = upgrade_key.replace('_', ' ').title() if upgrade_key else "Upgrade"
                    self.scene_manager.show_message(f"Upgraded {label}!", (0, 255, 0))
                else:
                    self.scene_manager.show_message("Not enough resources!", (255, 100, 100))
                
                return True
        
        return False

    def _handle_right_click(self, mouse_pos):
        # Convert screen space to world space logic
        # Move Command
        for ent, (sel, mov) in self.world.get_components(Selectable, Movement):
            if not sel.selected:
                continue

            trans = self.world.component_for_entity(ent, Transform)
            path = self.scene_manager.get_path(trans.x, trans.y, mouse_pos[0], mouse_pos[1])
            mov.path = path
            if path:
                mov.target_x, mov.target_y = path[0]
            else:
                mov.target_x = mouse_pos[0]
                mov.target_y = mouse_pos[1]
            mov.moving = True

    def _get_entity_at(self, pos):
        # Find highest layer entity at position
        mx, my = pos
        found_ent = None
        max_layer = -1
        
        for ent, (trans, ident) in self.world.get_components(Transform, Identity):
            # Allow selecting any entity (player, enemy, neutral)
            dist = math.hypot(trans.x - mx, trans.y - my)
            if dist < trans.radius + 5: # Small buffer
                 # Check render layer if available
                layer = 0
                if self.world.has_component(ent, Renderable):
                    layer = self.world.component_for_entity(ent, Renderable).layer
                
                if layer > max_layer:
                    max_layer = layer
                    found_ent = ent
        
        return found_ent

    def _select_single(self, ent):
        # Deselect all others first
        for e, sel in self.world.get_component(Selectable):
            sel.selected = False
            
        # Select target
        if self.world.has_component(ent, Selectable):
            self.world.component_for_entity(ent, Selectable).selected = True
            
            # Calculate initial panel position based on current mouse position
            mouse_pos = pygame.mouse.get_pos()
            
            # Panel dimensions (must match render system calculations)
            button_width = 180
            panel_width = button_width + 20
            
            # Estimate panel height (title + potential upgrade buttons)
            # This is a rough estimate since we don't know upgrade count yet
            estimated_panel_height = 200  # Reasonable max height
            
            # Position panel near cursor (top-left corner offset)
            panel_x = mouse_pos[0] - 10
            panel_y = mouse_pos[1] - 10
            
            # Keep within screen bounds
            if panel_x + panel_width > SCREEN_WIDTH:
                panel_x = SCREEN_WIDTH - panel_width - 5
            if panel_y + estimated_panel_height > SCREEN_HEIGHT:
                panel_y = SCREEN_HEIGHT - estimated_panel_height - 5
            
            panel_x = max(5, panel_x)
            panel_y = max(5, panel_y)
            
            # Store position for render system
            self.scene_manager.upgrade_panel_position = (panel_x, panel_y)
            
            # Show Panel
            self.scene_manager.upgrade_panel_show_time = self.scene_manager.game_time

    def _finish_selection(self):
        # Calculate selection rect
        x1, y1 = self.drag_start
        x2, y2 = self.drag_current
        left, right = min(x1, x2), max(x1, x2)
        top, bottom = min(y1, y2), max(y1, y2)

        # Deselect all first (MVP simple behavior)
        for ent, sel in self.world.get_component(Selectable):
            sel.selected = False

        # Select units inside rect
        has_selection = False
        for ent, (trans, ident, sel) in self.world.get_components(Transform, Identity, Selectable):
            if not (sel.selection_mask & SELECT_DRAG):
                continue

            if ident.faction == self.scene_manager.player_faction_id and ident.type == 'unit':
                if left < trans.x < right and top < trans.y < bottom:
                    sel.selected = True
                    has_selection = True
        
        # Show upgrade panel if units were selected
        if has_selection:
            self.scene_manager.upgrade_panel_show_time = self.scene_manager.game_time

    def _spawn_unit_burst(self, x, y):
        # Burst Spawn logic
        player_id = self.scene_manager.player_faction_id
        res = self.scene_manager.resources.get(player_id, 0)
        burst_count = 1 + int(res / 10)
        burst_count = min(burst_count, 10)
        
        success = True
        for _ in range(burst_count):
            if not self.scene_manager.spawn_unit(x, y):
                success = False
                break
        
        if not success:
            mouse_pos = pygame.mouse.get_pos()
            self.scene_manager.add_floating_message("UNIT CAP REACHED", mouse_pos[0], mouse_pos[1] - 30)
