"""
ECS Systems handling the game logic.
"""
import pygame
import esper
import math
import random
from config import *
from components import *
from spatial_hash import SpatialHash





class MovementSystem(esper.Processor):
    def __init__(self, spatial_hash):
        self.spatial_hash = spatial_hash

    def process(self):
        dt = min(1/30, self.world.scene_manager.dt)
        
        # 1. Update Spatial Hash
        self.spatial_hash.clear()
        for ent, (trans, ident) in self.world.get_components(Transform, Identity):
            if ident.type in ['unit', 'obstacle', 'castle', 'resource']:
                # Pass radius to handle large obstacles correctly
                self.spatial_hash.insert(ent, trans.x, trans.y, trans.radius)

        # 2. Process Physics
        for ent, (trans, vel, mov, ident) in self.world.get_components(Transform, Velocity, Movement, Identity):
            # A. Separation Force (Push away from neighbors)
            sep_x, sep_y = 0, 0
            neighbors = self.spatial_hash.query_nearby(trans.x, trans.y)
            count = 0

            for other_id in neighbors:
                if other_id == ent: continue

                try:
                    other_trans = self.world.component_for_entity(other_id, Transform)
                    other_ident = self.world.component_for_entity(other_id, Identity)
                except KeyError:
                    continue  # Entity might have died mid-frame

                # Only separate from other units (allow overlapping castles/resources)
                # This prevents units from getting stuck when pathfinding through friendly structures
                if other_ident.type != 'unit':
                    continue

                dx = trans.x - other_trans.x
                dy = trans.y - other_trans.y
                dist_sq = dx * dx + dy * dy
                min_dist = trans.radius + other_trans.radius

                if 0 < dist_sq < min_dist ** 2:
                    dist = math.sqrt(dist_sq)
                    if dist < 0.001: dist = 0.001 # Prevent div by zero
                    
                    force = (min_dist - dist) / dist * SEPARATION_FORCE
                    force = min(force, SEPARATION_FORCE * 5) # Cap force
                    
                    sep_x += (dx / dist) * force
                    sep_y += (dy / dist) * force
                    count += 1

            # Apply Separation
            vel.vx += sep_x * dt
            vel.vy += sep_y * dt

            # B. Hard Collision with Obstacles (Rivers/Mountains)
            # Query broadly
            obstacles = self.spatial_hash.query_nearby(trans.x, trans.y)
            for obs_id in obstacles:
                 if obs_id == ent: continue
                 try:
                     obs_ident = self.world.component_for_entity(obs_id, Identity)
                     if obs_ident.type == 'obstacle':
                         obs_trans = self.world.component_for_entity(obs_id, Transform)
                         
                         dx = trans.x - obs_trans.x
                         dy = trans.y - obs_trans.y
                         
                         # Check overlap with obstacle
                         dist = math.hypot(dx, dy)
                         min_dist = trans.radius + obs_trans.radius
                         
                         if dist < min_dist and dist > 0.001:
                             # Strong push out - be more aggressive 
                             # Use a multiplier to ensure units clear obstacles quickly
                             push_multiplier = 1.5  # Push harder to clear obstacles
                             push = (min_dist - dist) * push_multiplier
                             
                             # Normalize direction
                             nx = dx / dist
                             ny = dy / dist
                             
                             # Apply pushback
                             trans.x += nx * push
                             trans.y += ny * push
                             
                             # Kill velocity towards the obstacle and add velocity away
                             dot = vel.vx * nx + vel.vy * ny
                             if dot < 0:
                                 # Remove velocity component towards obstacle
                                 vel.vx -= dot * nx
                                 vel.vy -= dot * ny
                                 # Add bounce-back velocity to get away from obstacle
                                 vel.vx += nx * abs(dot) * 0.5
                                 vel.vy += ny * abs(dot) * 0.5
                             
                 except KeyError: pass

            # C. Move towards Target
            if mov.moving and mov.target_x is not None:
                # First, validate if current waypoint is inside an obstacle
                # If so, skip to next waypoint to avoid getting stuck
                waypoint_blocked = False
                nearby = self.spatial_hash.query_nearby(mov.target_x, mov.target_y)
                for obs_id in nearby:
                    try:
                        obs_ident = self.world.component_for_entity(obs_id, Identity)
                        if obs_ident.type == 'obstacle':
                            obs_trans = self.world.component_for_entity(obs_id, Transform)
                            dist_to_waypoint = math.hypot(mov.target_x - obs_trans.x, mov.target_y - obs_trans.y)
                            # Check if waypoint is inside obstacle (with unit radius buffer)
                            if dist_to_waypoint < obs_trans.radius + trans.radius + 5:
                                waypoint_blocked = True
                                break
                    except KeyError:
                        pass
                
                # Skip blocked waypoints
                if waypoint_blocked and mov.path:
                    mov.path.pop(0)
                    if mov.path:
                        mov.target_x, mov.target_y = mov.path[0]
                    else:
                        mov.moving = False
                        mov.target_x = None
                        vel.vx *= 0.5
                        vel.vy *= 0.5
                
                # Normal waypoint navigation
                if mov.moving and mov.target_x is not None:
                    dx = mov.target_x - trans.x
                    dy = mov.target_y - trans.y
                    dist = math.hypot(dx, dy)

                    if dist < 10:  # Arrived (increased threshold for better reliability)
                        # Check next waypoint
                        if mov.path:
                            mov.path.pop(0)
                            if mov.path:
                                mov.target_x, mov.target_y = mov.path[0]
                            else:
                                mov.moving = False
                                mov.target_x = None # Clear target
                                vel.vx *= 0.5
                                vel.vy *= 0.5
                        else:
                            mov.moving = False
                            mov.target_x = None
                            vel.vx *= 0.5  # Slow down
                            vel.vy *= 0.5
                    else:
                        multiplier = 1.0
                        if self.world.scene_manager.sudden_death:
                            multiplier *= 3.0

                        speed = mov.speed * multiplier
                        vel.vx += (dx / dist) * speed * 5.0 * dt  # Steering
                        vel.vy += (dy / dist) * speed * 5.0 * dt

            # D. Friction/Damping
            vel.vx *= 0.90
            vel.vy *= 0.90

            # E. Apply Velocity
            trans.x += vel.vx * dt
            trans.y += vel.vy * dt

            # F. Clamp to Screen
            trans.x = max(trans.radius, min(SCREEN_WIDTH - trans.radius, trans.x))
            trans.y = max(trans.radius, min(SCREEN_HEIGHT - trans.radius, trans.y))


class CombatSystem(esper.Processor):
    def __init__(self, spatial_hash):
        self.spatial_hash = spatial_hash

    def process(self):
        dt = self.world.scene_manager.dt

        # Cooldown management
        for ent, stats in self.world.get_component(Stats):
            if stats.current_cd > 0:
                stats.current_cd -= dt

        # Combat Logic - Units attacking
        for ent, (trans, ident, stats, vel) in self.world.get_components(Transform, Identity, Stats, Velocity):
            if ident.type != 'unit': continue  # Only units have Velocity

            targets = self.spatial_hash.query_nearby(trans.x, trans.y)

            closest_enemy = None
            closest_dist = 9999

            for target_id in targets:
                if target_id == ent: continue
                try:
                    t_ident = self.world.component_for_entity(target_id, Identity)
                    t_trans = self.world.component_for_entity(target_id, Transform)
                    t_stats = self.world.component_for_entity(target_id, Stats)
                except KeyError:
                    continue

                # Units can attack enemy units, castles, and neutral resource points
                is_enemy = (t_ident.faction != ident.faction and t_ident.faction != FACTION_NEUTRAL) or \
                           (t_ident.faction == FACTION_NEUTRAL and t_ident.type == 'resource')
                
                if is_enemy and not t_stats.dead:
                    dx = trans.x - t_trans.x
                    dy = trans.y - t_trans.y
                    dist = math.sqrt(dx * dx + dy * dy)

                    if dist < stats.attack_range + t_trans.radius:
                        if dist < closest_dist:
                            closest_dist = dist
                            closest_enemy = target_id

            # Attack
            if closest_enemy is not None:
                # Stop moving to fight
                vel.vx *= 0.1
                vel.vy *= 0.1

                if stats.current_cd <= 0:
                    enemy_ident = self.world.component_for_entity(closest_enemy, Identity)
                    enemy_stats = self.world.component_for_entity(closest_enemy, Stats)
                    enemy_trans = self.world.component_for_entity(closest_enemy, Transform)
                    
                    # Check if this is a ranged attack (range > 20)
                    is_ranged = stats.attack_range > 20
                    
                    if is_ranged:
                        # Spawn projectile for ranged attack
                        attacker_color = self.world.scene_manager.get_faction_color(ident.faction)
                        self.world.scene_manager.spawn_projectile(
                            trans.x, trans.y,
                            enemy_trans.x, enemy_trans.y,
                            stats.attack_dmg,
                            closest_enemy,
                            attacker_color,
                            ident.faction  # Pass attacker faction
                        )
                    else:
                        # Melee attack - instant damage
                        enemy_stats.hp -= stats.attack_dmg
                    
                    stats.current_cd = stats.attack_cd

                    # Check for death and create kill request
                    if enemy_stats.hp <= 0:
                        enemy_stats.dead = True
                        
                        # Create kill request for CleanupSystem to handle
                        self.world.create_entity(
                            KillRequest(
                                killer_faction=ident.faction,
                                killed_entity=closest_enemy
                            )
                        )

        # Static Defenses (Castles & Resources)
        for ent, (trans, ident, stats) in self.world.get_components(Transform, Identity, Stats):
            if ident.type not in ['castle', 'resource']: continue

            # Determine targets
            targets = self.spatial_hash.query_nearby(trans.x, trans.y)
            enemy_units = []
            
            for target_id in targets:
                if target_id == ent: continue
                try:
                    t_ident = self.world.component_for_entity(target_id, Identity)
                    t_trans = self.world.component_for_entity(target_id, Transform)
                    t_stats = self.world.component_for_entity(target_id, Stats)
                except KeyError:
                    continue
                
                # Filter for living units
                if t_ident.type == 'unit' and not t_stats.dead:
                    # Check hostility
                    is_enemy = False
                    if ident.faction == FACTION_NEUTRAL:
                        is_enemy = True # Neutral defenses hate everyone
                    else:
                        if t_ident.faction != ident.faction and t_ident.faction != FACTION_NEUTRAL:
                            is_enemy = True # Faction defenses hate other factions (ignore neutral)
                    
                    if is_enemy:
                        dx = trans.x - t_trans.x
                        dy = trans.y - t_trans.y
                        dist = math.sqrt(dx * dx + dy * dy)
                        
                        if dist < stats.attack_range + t_trans.radius:
                            enemy_units.append(target_id)
            
            
            # Attack random enemy unit
            if enemy_units and stats.current_cd <= 0:
                target = random.choice(enemy_units)
                target_stats = self.world.component_for_entity(target, Stats)
                target_trans = self.world.component_for_entity(target, Transform)
                
                # Castles/resources always use ranged attacks (spawn projectile)
                attacker_color = self.world.scene_manager.get_faction_color(ident.faction)
                self.world.scene_manager.spawn_projectile(
                    trans.x, trans.y,
                    target_trans.x, target_trans.y,
                    stats.attack_dmg,
                    target,
                    attacker_color,
                    ident.faction  # Pass attacker faction
                )
                
                stats.current_cd = stats.attack_cd


class ResourceSystem(esper.Processor):
    def process(self):
        dt = self.world.scene_manager.dt
        sm = self.world.scene_manager

        # Generate Resources
        for ent, (gen, ident) in self.world.get_components(ResourceGenerator, Identity):
            if ident.faction != FACTION_NEUTRAL:  # Generate for any non-neutral faction
                multiplier = 1.0  # Could add upgrade logic here
                gen.accumulated += gen.rate * multiplier * dt
                if gen.accumulated >= 1.0:
                    sm.resources[ident.faction] += int(gen.accumulated)
                    gen.accumulated %= 1.0



class ConstructionSystem(esper.Processor):
    def process(self):
        dt = self.world.scene_manager.dt
        
        for ent, (site, trans) in self.world.get_components(ConstructionSite, Transform):
            # Verify Units are Alive
            alive_count = 0
            for uid in site.units_ids:
                try:
                    stats = self.world.component_for_entity(uid, Stats)
                    if not stats.dead:
                        alive_count += 1
                except KeyError:
                    pass
            
            if alive_count < len(site.units_ids):
                # Construction Failed
                self.world.scene_manager.show_message("Construction Interrupted", (255, 50, 50))
                
                # Release survivors (stop them from being frozen if they are still alive)
                for uid in site.units_ids:
                    try:
                        stats = self.world.component_for_entity(uid, Stats)
                        if not stats.dead:
                            # Unfreeze
                            if self.world.has_component(uid, Movement):
                                mov = self.world.component_for_entity(uid, Movement)
                                # Just ensure they can move again (though moving=False is already 'idle')
                                pass
                    except KeyError:
                        pass
                        
                self.world.delete_entity(ent)
                continue

            site.elapsed += dt
            if site.elapsed >= site.total_time:
                # Finish Build
                # Consume Units
                for uid in site.units_ids:
                    try:
                        # Check if already dead (from CombatSystem)
                        stats = self.world.component_for_entity(uid, Stats)
                        if not stats.dead:
                            self.world.delete_entity(uid)
                    except KeyError:
                        pass 
                
                # Create Castle
                new_castle = self.world.scene_manager.create_entity('castle', trans.x, trans.y, site.faction)
                
                # Attach AIController
                is_player = (site.faction == self.world.scene_manager.player_faction_id)
                self.world.add_component(new_castle, 
                    AIController(auto_spawn=not is_player, auto_attack=not is_player))
                
                # Destroy Site
                self.world.delete_entity(ent)
                print("Construction Complete!")


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
        is_player_owned = (selected_faction == sm.player_faction_id)
        upgrade_defs = []
        panel_title = ""
        
        if selected_type == 'castle':
            if is_player_owned:
                panel_title = "Your Castle"
                
                # Check for Autopilot
                has_autopilot = False
                if selected_entity is not None and self.world.has_component(selected_entity, AIController):
                    has_autopilot = True
                
                autopilot_btn = ('stop autopilot', None, 'toggle_autopilot', (100, 100, 100)) if has_autopilot \
                           else ('autopilot', None, 'toggle_autopilot', (150, 150, 150))

                upgrade_defs = [
                    autopilot_btn,
                    ('Castle HP', 'castle_hp', 'upgrade_castle_hp', (100, 150, 255)),
                    ('Castle Dmg', 'castle_dmg', 'upgrade_castle_dmg', (255, 100, 100)),
                    ('Castle CD', 'castle_cd', 'upgrade_castle_cd', (150, 255, 150)),
                ]
            else:
                panel_title = "Enemy Castle"
                upgrade_defs = []
        elif selected_type == 'resource':
            if is_player_owned:
                panel_title = "Resource Point (Captured)"
                upgrade_defs = [
                    ('Res Speed', 'resource_rate', 'upgrade_resource_rate', (255, 215, 0)),
                ]
            else:
                panel_title = "Resource Point"
                upgrade_defs = []
        elif selected_type == 'unit':
            if is_player_owned:
                panel_title = "Your Units"
                upgrade_defs = [
                    ('Unit HP', 'unit_hp', 'upgrade_unit_hp', (100, 150, 255)),
                    ('Unit Damage', 'unit_dmg', 'upgrade_unit_dmg', (255, 100, 100)),
                    ('Attack Speed', 'unit_cd', 'upgrade_unit_cd', (150, 255, 150)),
                    ('Attack Range', 'unit_range', 'upgrade_unit_range', (255, 150, 255)),
                    ('Move Speed', 'unit_speed', 'upgrade_unit_speed', (255, 200, 100)),
                ]
            else:
                panel_title = "Enemy Units"
                upgrade_defs = []
        elif selected_type == 'empty_tile':
            panel_title = "Empty Tile"
            upgrade_defs = [
                ('Build Castle', None, 'build_castle', (100, 200, 100)),
            ]
        
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


class AISystem(esper.Processor):
    def __init__(self, scene_manager):
        self.sm = scene_manager
        self.timer = 0
        self.expansion_timer = 0
        self.upgrade_timer = 0  # AI upgrade decision timer

    def _count_nearby_allies(self, x, y, faction):
        count = 0 
        neighbors = self.sm.spatial_hash.query_nearby(x, y)
        for other in neighbors:
             try:
                 if self.world.has_component(other, Identity):
                     o_ident = self.world.component_for_entity(other, Identity)
                     if o_ident.faction == faction and o_ident.type == 'unit':
                         count += 1
             except KeyError:
                 pass
        return count

    def _is_valid_build_site(self, x, y):
        if not (50 < x < SCREEN_WIDTH - 50 and 50 < y < SCREEN_HEIGHT - 50): return False
        for ent, (trans, ident) in self.world.get_components(Transform, Identity):
             if ident.type in ['castle', 'resource', 'obstacle']:
                 dist = math.hypot(trans.x - x, trans.y - y)
                 if dist < trans.radius + CASTLE_RADIUS + 30: return False
        return True

    def _execute_build(self, faction, x, y, units):
        if self.sm.resources.get(faction, 0) < CASTLE_BUILD_COST: return
        self.sm.resources[faction] -= CASTLE_BUILD_COST
        unit_ids = []
        for u in units:
             unit_ids.append(u)
             if self.world.has_component(u, Movement) and self.world.has_component(u, Transform):
                 mov = self.world.component_for_entity(u, Movement)
                 trans = self.world.component_for_entity(u, Transform)
                 path = self.sm.get_path(trans.x, trans.y, x, y)
                 mov.path = path
                 if path:
                     mov.target_x, mov.target_y = path[0]
                 else:
                     mov.target_x = x; mov.target_y = y
                 mov.moving = True
        
        self.world.create_entity(
            Transform(x=x, y=y, radius=CASTLE_RADIUS),
            ConstructionSite(total_time=CASTLE_CONSTRUCTION_TIME, elapsed=0.0, units_ids=unit_ids, faction=faction),
            Renderable(color=(100, 100, 100), shape='square', layer=0)
        )

    def _try_expansion(self, faction):
        if self.sm.resources.get(faction, 0) < CASTLE_BUILD_COST + 100:
            return

        candidates = []
        for ent, (trans, ident) in self.world.get_components(Transform, Identity):
            if ident.type in ['resource', 'castle']:
                 candidates.append(trans)
        
        random.shuffle(candidates)
        
        for target_trans in candidates:
             # For resource points, check units at an offset position (where castle would be built)
             # This avoids trying to build at the exact resource point location
             check_x = target_trans.x
             check_y = target_trans.y
             
             # If it's a resource point, offset the check position
             try:
                 target_ent = None
                 for ent, (t, i) in self.world.get_components(Transform, Identity):
                     if t == target_trans:
                         target_ent = ent
                         break
                 
                 if target_ent:
                     target_ident = self.world.component_for_entity(target_ent, Identity)
                     if target_ident.type == 'resource':
                         # Offset by 120 in a random direction for resource points
                         angle = random.uniform(0, 6.28)
                         check_x = target_trans.x + math.cos(angle) * 120
                         check_y = target_trans.y + math.sin(angle) * 120
             except KeyError:
                 pass
             
             nearby_units = []
             neighbors = self.sm.spatial_hash.query_nearby(check_x, check_y)
             for nid in neighbors:
                 try:
                     u_ident = self.world.component_for_entity(nid, Identity)
                     if u_ident.faction == faction and u_ident.type == 'unit':
                         nearby_units.append(nid)
                 except KeyError: pass
             
             if len(nearby_units) >= CASTLE_BUILD_REQ:
                 # Tactical Placement: Towards nearest enemy
                 target_angle = random.uniform(0, 6.28)
                 best_dist = float('inf')
                 enemy_loc = None
                 
                 for e_ent, (e_trans, e_ident) in self.world.get_components(Transform, Identity):
                     if e_ident.faction != faction and e_ident.type == 'castle':
                         d = math.hypot(e_trans.x - target_trans.x, e_trans.y - target_trans.y)
                         if d < best_dist:
                             best_dist = d
                             enemy_loc = e_trans
                 
                 if enemy_loc:
                     target_angle = math.atan2(enemy_loc.y - target_trans.y, enemy_loc.x - target_trans.x)
                     target_angle += random.uniform(-0.5, 0.5)

                 dist = 120
                 build_x = target_trans.x + math.cos(target_angle) * dist
                 build_y = target_trans.y + math.sin(target_angle) * dist
                 
                 if self._is_valid_build_site(build_x, build_y):
                     self._execute_build(faction, build_x, build_y, nearby_units[:CASTLE_BUILD_REQ])
                     return

    def _try_upgrades(self, faction):
        """AI decision logic for purchasing upgrades"""
        resources = self.sm.resources.get(faction, 0)

        # higher resource higher chance to upgrade
        k = 2 * STARTING_RESOURCES
        val = 0.4 + (k - resources) / k
        if random.uniform(0, 1) < val:
            return
        # print(val)
        
        # Get upgrade system
        upgrade_sys = None
        for processor in self.world._processors:
            if processor.__class__.__name__ == 'UpgradeSystem':
                upgrade_sys = processor
                break

        if not upgrade_sys:
            return
        upgrades = self.sm.faction_upgrades[faction]
        
        # Max out unit upgrades (gather all affordable options)
        affordable_upgrades = []
        
        for upgrade_type in ['unit_hp', 'unit_dmg', 'unit_cd', 'unit_speed']:
            if upgrades[upgrade_type] < MAX_UPGRADE_LEVEL:
                cost = upgrade_sys.get_upgrade_cost(upgrades[upgrade_type])
                if resources >= cost:
                    affordable_upgrades.append((upgrade_type, cost))
        
        # Also consider range (with special cost)
        if upgrades['unit_range'] < MAX_UPGRADE_LEVEL:
            cost = upgrade_sys.get_range_upgrade_cost(upgrades['unit_range'])
            if resources >= cost:
                affordable_upgrades.append(('unit_range', cost))
        
        # Pick randomly from affordable upgrades (weighted by inverse cost - cheaper = more likely)
        if affordable_upgrades:
            # Slight preference for cheaper upgrades, but still random
            choice = random.choice(affordable_upgrades)
            upgrade_type = choice[0]
            
            if upgrade_type == 'unit_hp':
                upgrade_sys.upgrade_unit_hp(faction)
            elif upgrade_type == 'unit_dmg':
                upgrade_sys.upgrade_unit_dmg(faction)
            elif upgrade_type == 'unit_cd':
                upgrade_sys.upgrade_unit_cd(faction)
            elif upgrade_type == 'unit_speed':
                upgrade_sys.upgrade_unit_speed(faction)
            elif upgrade_type == 'unit_range':
                upgrade_sys.upgrade_unit_range(faction)
            return

    def process(self):
        dt = self.sm.dt
        self.timer += dt
        self.expansion_timer += dt

        check_expansion = False
        if self.expansion_timer > 5.0:
            self.expansion_timer = 0
            check_expansion = True

        if self.timer < 0.2:
            return
        self.timer = 0

        # 1. Global Castle Behavior (Defensive Garrison)
        # Ensures basic defense for ALL castles (Player & AI)
        for ent, (trans, ident) in self.world.get_components(Transform, Identity):
            if ident.type == 'castle':
                faction = ident.faction
                res = self.sm.resources.get(faction, 0)
                if res >= UNIT_COST:
                    count = self._count_nearby_allies(trans.x, trans.y, faction)
                    if count < 10:
                        self.sm.spawn_unit(trans.x, trans.y, faction)

        # 2. AI Strategic Decisions (Commanders)
        # Pre-calc strengths
        unit_counts = {}
        for ent, ident in self.world.get_component(Identity):
            if ident.type == 'unit':
                unit_counts[ident.faction] = unit_counts.get(ident.faction, 0) + 1

        processed_factions = set()
        upgrade_processed_factions = set()  # Separate set for upgrades
        for ent, (ai, trans, ident) in self.world.get_components(AIController, Transform, Identity):
            if not ai.active:
                continue

            faction = ident.faction

            # Expansion Check
            if check_expansion and ai.auto_spawn and faction not in processed_factions:
                processed_factions.add(faction)
                self._try_expansion(faction)

            # Upgrade Check (for AI factions, once per faction)
            if faction != self.sm.player_faction_id and faction not in upgrade_processed_factions:
                upgrade_processed_factions.add(faction)
                self._try_upgrades(faction)

            # A. Surplus / Defense Spawning
            res = self.sm.resources.get(faction, 0)

            # Check damage
            is_damaged = False
            try:
                stats = self.world.component_for_entity(ent, Stats)
                if stats.hp < stats.max_hp: is_damaged = True
            except KeyError: pass

            if ai.auto_spawn:
                # Logic: Spend freely if weak or threatened. Save for expansion/upgrades if strong.
                threshold = 100  # Reserve for upgrades
                if is_damaged:
                    threshold = 20  # Emergency - but still save a bit
                elif unit_counts.get(faction, 0) >= 20:
                    threshold = CASTLE_BUILD_COST + 300  # Save up for castle

                # Reserve additional resources for upgrades (game-time based)
                game_time = self.sm.game_time
                if game_time > 60:  # After 1 minute, start saving for upgrades
                    threshold = max(threshold, 30)  # Keep at least 30
                if game_time > 120:  # After 2 minutes
                    threshold = max(threshold, 50)  # Keep at least 50

                if res > threshold:
                    # Spend excess, but don't dump everything
                    max_spawns = (res - threshold) // UNIT_COST
                    max_spawns = min(max_spawns, 5)  # Limit burst spawning
                    for _ in range(max_spawns):
                        if self.sm.resources.get(faction, 0) >= UNIT_COST:
                            self.sm.spawn_unit(trans.x, trans.y, faction)

            # B. Command Units (Commander Logic)
            if not ai.auto_attack:
                continue

            # Find targets
            my_strength = unit_counts.get(faction, 0)
            targets = []
            for t_ent, (t_trans, t_ident) in self.world.get_components(Transform, Identity):
                if t_ident.faction != faction and t_ident.type in ['resource', 'castle', 'unit']:

                    priority = 10
                    local_threat = 0

                    if t_ident.type == 'resource':
                        # if t_ident.faction == FACTION_NEUTRAL: priority = 60 # High priority expansion
                        # else: priority = 40
                        priority = 60
                    elif t_ident.type == 'castle': priority = 60
                    elif t_ident.type == 'unit': priority = 20

                    # Local Threat Assessment: Scan for defenders
                    if t_ident.type in ['castle', 'resource'] and t_ident.faction != FACTION_NEUTRAL:
                         neighbors = self.sm.spatial_hash.query_nearby(t_trans.x, t_trans.y)
                         for nid in neighbors:
                              try:
                                  n_ident = self.world.component_for_entity(nid, Identity)
                                  if n_ident.faction == t_ident.faction and n_ident.type == 'unit':
                                       local_threat += 1
                              except KeyError: pass

                    targets.append((t_trans, priority, t_ident.type, t_ident.faction, local_threat))

            if not targets: continue

            # Filter Sample
            important = [t for t in targets if t[2] in ['castle', 'resource']]
            units = [t for t in targets if t[2] == 'unit']

            if len(units) > 10:
                units = random.sample(units, 10)

            final_targets = important + units

            # Calculate Strategic Weights (Global Distribution)
            scored_targets = []

            for t_trans, prio, t_type, t_faction, t_threat in final_targets:
                 # Value = Priority - Threat
                 val = (prio * 10) - (t_threat * 10)

                 # Distance from Base (Commander)
                 d = math.hypot(t_trans.x - trans.x, t_trans.y - trans.y)
                 val -= d * 0.5

                 if val > 10: # Minimum viability
                     scored_targets.append((t_trans, val))

            if not scored_targets: continue

            # Constraint: Max 2 targets, must be comparable (>50% score)
            scored_targets.sort(key=lambda x: x[1], reverse=True)
            weighted_targets = [scored_targets[0]]
            if len(scored_targets) > 1:
                 if scored_targets[1][1] > 0.5 * scored_targets[0][1]:
                     weighted_targets.append(scored_targets[1])

            total_weight = sum(x[1] for x in weighted_targets)

            # Command Idle Units using Probability Distribution
            for u_ent, (u_ident, u_mov, u_trans) in self.world.get_components(Identity, Movement, Transform):
                 if u_ident.faction == faction and not u_mov.moving:
                     # Stochastic Selection
                     r = random.uniform(0, total_weight)
                     acc = 0
                     target = weighted_targets[0][0]
                     for t, w in weighted_targets:
                         acc += w
                         if r <= acc:
                             target = t
                             break

                     path = self.sm.get_path(u_trans.x, u_trans.y, target.x, target.y)
                     u_mov.path = path
                     if path:
                         u_mov.target_x, u_mov.target_y = path[0]
                     else:
                         u_mov.target_x = target.x
                         u_mov.target_y = target.y
                     u_mov.moving = True


class WinConditionSystem(esper.Processor):
    def __init__(self, scene_manager):
        self.sm = scene_manager
        self.check_timer = 0.0
        self.check_interval = 2.0  # Check every 2 seconds

    def process(self):
        # Don't check if game is already over
        if self.sm.game_over:
            return

        dt = self.sm.dt
        self.check_timer += dt

        # Only check periodically to save performance
        if self.check_timer >= self.check_interval:
            self.check_timer = 0.0
            
            # Count entities per faction (excluding neutral and resource points)
            faction_counts = {}
            
            for ent, ident in self.world.get_component(Identity):
                # Only count units and castles for win condition
                # Resources don't count, and neutral faction doesn't participate
                if ident.faction != FACTION_NEUTRAL and ident.type in ['unit', 'castle']:
                    if ident.faction not in faction_counts:
                        faction_counts[ident.faction] = 0
                    faction_counts[ident.faction] += 1
            
            # Check if only one faction remains
            active_factions = [f for f, count in faction_counts.items() if count > 0]
            
            if len(active_factions) == 1:
                # We have a winner!
                winner = active_factions[0]
                self.sm.game_over = True
                self.sm.winner = winner
                winner_name = "PLAYER" if winner == self.sm.player_faction_id else f"AI FACTION {winner}"
                print(f"\n{'='*50}")
                print(f"GAME OVER! {winner_name} WINS!")
                print(f"Victory Faction ID: {winner}")
                print(f"{'='*50}\n")
            elif len(active_factions) == 0:
                # Edge case: everyone died (draw)
                self.sm.game_over = True
                self.sm.winner = None
                print(f"\n{'='*50}")
                print(f"GAME OVER! IT'S A DRAW!")
                print(f"{'='*50}\n")
