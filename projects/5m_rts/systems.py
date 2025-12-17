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


class InputSystem(esper.Processor):
    def __init__(self, scene_manager):
        self.scene_manager = scene_manager  # To access resources
        self.selecting = False
        self.drag_start = (0, 0)
        self.drag_current = (0, 0)
        self.hold_timer = 0.0
        self.holding_build = False

    def process(self):
        dt = self.scene_manager.dt
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        mouse_buttons = pygame.mouse.get_pressed()  # (Left, Middle, Right)

        # 1. Spawn Unit (Tap on Castle)
        # 2. Select (Drag Box)
        # 3. Move (Right Click for MVP simplicity, or Touch-Drag logic)

        events = self.scene_manager.events
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left Click
                    self.selecting = True
                    self.drag_start = mouse_pos
                    self.drag_current = mouse_pos
                    self.hold_timer = 0.0

                    # Check Castle Click
                    clicked_castle = False
                    for ent, (trans, ident) in self.world.get_components(Transform, Identity):
                        if ident.faction == self.scene_manager.player_faction_id and ident.type == 'castle':
                            dist = math.hypot(trans.x - mouse_pos[0], trans.y - mouse_pos[1])
                            if dist < trans.radius + 5:
                                # Burst Spawn logic
                                res = self.scene_manager.resources.get(self.scene_manager.player_faction_id, 0)
                                burst_count = 1 + int(res / 10)
                                burst_count = min(burst_count, 10)
                                for _ in range(burst_count):
                                    self.scene_manager.spawn_unit(trans.x, trans.y)
                                
                                clicked_castle = True
                                self.selecting = False  # Cancel selection if clicking castle
                                break

                if event.button == 3:  # Right Click (Move Command)
                    # Convert screen space to world space logic
                    for ent, (sel, mov) in self.world.get_components(Selectable, Movement):
                        if sel.selected:
                            trans = self.world.component_for_entity(ent, Transform)
                            path = self.scene_manager.get_path(trans.x, trans.y, mouse_pos[0], mouse_pos[1])
                            mov.path = path
                            if path:
                                mov.target_x, mov.target_y = path[0]
                            else:
                                mov.target_x = mouse_pos[0]
                                mov.target_y = mouse_pos[1]
                            mov.moving = True

            elif event.type == pygame.MOUSEMOTION:
                if self.selecting:
                    self.drag_current = mouse_pos

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and self.selecting:
                    self._finish_selection()
                    self.selecting = False
                    self.holding_build = False

        # Handle Hold to Build Castle logic
        if self.selecting and not self.holding_build:
            # If mouse hasn't moved much and held long enough
            dist_sq = (self.drag_start[0] - self.drag_current[0]) ** 2 + (
                        self.drag_start[1] - self.drag_current[1]) ** 2
            if dist_sq < 100:  # Threshold
                self.hold_timer += dt
                if self.hold_timer > CASTLE_CONFIRM_TIME:
                    self._start_construction()
                    self.holding_build = True  # Prevent spamming
            else:
                self.hold_timer = 0.0

    def _finish_selection(self):
        # Calculate selection rect
        x1, y1 = self.drag_start
        x2, y2 = self.drag_current
        left, right = min(x1, x2), max(x1, x2)
        top, bottom = min(y1, y2), max(y1, y2)

        # Deselect all first unless shift held (omitted for MVP)
        for ent, sel in self.world.get_component(Selectable):
            sel.selected = False

        # Select units inside rect
        for ent, (trans, ident, sel) in self.world.get_components(Transform, Identity, Selectable):
            if ident.faction == self.scene_manager.player_faction_id and ident.type == 'unit':
                if left < trans.x < right and top < trans.y < bottom:
                    sel.selected = True

    def _start_construction(self):
        # Check if we have > 10 selected units
        selected_units = [] # List of (entity, transform)

        for ent, (trans, sel) in self.world.get_components(Transform, Selectable):
            if sel.selected:
                selected_units.append((ent, trans))

        if len(selected_units) >= CASTLE_BUILD_REQ:
            # 1. Calculate centroid first (potential build site)
            units_to_sacrifice = selected_units[:CASTLE_BUILD_REQ]
            center_x, center_y = 0, 0
            for _, trans in units_to_sacrifice:
                center_x += trans.x
                center_y += trans.y
            center_x /= len(units_to_sacrifice)
            center_y /= len(units_to_sacrifice)

            # 2. Check Overlap
            for ent, (trans, ident) in self.world.get_components(Transform, Identity):
                if ident.type in ['castle', 'resource', 'obstacle']:
                    dist = math.hypot(trans.x - center_x, trans.y - center_y)
                    # Use a safe buffer
                    min_dist = trans.radius + CASTLE_RADIUS + 10
                    if dist < min_dist:
                        print("Cannot build here: Structure overlap!")
                        self.scene_manager.show_message("Cannot build: Overlap!", (255, 50, 50))
                        return

            # 3. Check Cost & Start Construction
            player_id = self.scene_manager.player_faction_id
            if self.scene_manager.resources[player_id] >= CASTLE_BUILD_COST:
                self.scene_manager.resources[player_id] -= CASTLE_BUILD_COST
                
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
        else:
            self.scene_manager.show_message(f"Need {CASTLE_BUILD_REQ} units!", (255, 50, 50))


class MovementSystem(esper.Processor):
    def __init__(self, spatial_hash):
        self.spatial_hash = spatial_hash

    def process(self):
        dt = self.world.scene_manager.dt
        
        # 1. Update Spatial Hash
        self.spatial_hash.clear()
        for ent, (trans, ident) in self.world.get_components(Transform, Identity):
            if ident.type in ['unit', 'obstacle', 'castle', 'resource']:
                self.spatial_hash.insert(ent, trans.x, trans.y)

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
                except KeyError:
                    continue  # Entity might have died mid-frame

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
                dx = mov.target_x - trans.x
                dy = mov.target_y - trans.y
                dist = math.hypot(dx, dy)

                if dist < 5:  # Arrived
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
                    enemy_stats.hp -= stats.attack_dmg
                    stats.current_cd = stats.attack_cd

                    if enemy_stats.hp <= 0:
                        enemy_stats.dead = True
                        
                        # Capture mechanics for strategic points
                        if enemy_ident.type == 'resource':
                            # Capture resource point - change faction and restore HP
                            enemy_ident.faction = ident.faction
                            enemy_stats.hp = enemy_stats.max_hp
                            enemy_stats.dead = False
                            
                            # Update color to match new faction
                            if self.world.has_component(closest_enemy, Renderable):
                                render = self.world.component_for_entity(closest_enemy, Renderable)
                                render.color = self.world.scene_manager.get_faction_color(ident.faction)
                            
                            # Add resource generator if captured
                            if not self.world.has_component(closest_enemy, ResourceGenerator):
                                self.world.add_component(closest_enemy, ResourceGenerator(rate=RES_GENERATION_RATE))
                        
                        elif enemy_ident.type == 'castle':
                            # Capture castle - change faction and restore HP
                            enemy_ident.faction = ident.faction
                            enemy_stats.hp = enemy_stats.max_hp
                            enemy_stats.dead = False
                            
                            # Update color to match new faction
                            if self.world.has_component(closest_enemy, Renderable):
                                render = self.world.component_for_entity(closest_enemy, Renderable)
                                render.color = self.world.scene_manager.get_faction_color(ident.faction)

                            # Update AI Controller
                            is_player = (ident.faction == self.world.scene_manager.player_faction_id)
                            if self.world.has_component(closest_enemy, AIController):
                                ai = self.world.component_for_entity(closest_enemy, AIController)
                                ai.auto_attack = not is_player
                                ai.auto_spawn = not is_player
                            else:
                                self.world.add_component(closest_enemy, 
                                    AIController(auto_spawn=not is_player, auto_attack=not is_player))
                        
                        elif enemy_ident.type == 'unit':
                            # Delete units when killed
                            self.world.delete_entity(closest_enemy)

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
                target_stats.hp -= stats.attack_dmg
                stats.current_cd = stats.attack_cd
                
                if target_stats.hp <= 0:
                    target_stats.dead = True
                    self.world.delete_entity(target)


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
                self.world.scene_manager.show_message("Construction Failed: Not enough units!", (255, 50, 50))
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

    def process(self):
        self.window.fill(COLOR_BG)

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

                pass

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
            if isinstance(sys, InputSystem):
                input_sys = sys
                break

        if input_sys and input_sys.selecting:
            rect = pygame.Rect(input_sys.drag_start, (
            input_sys.drag_current[0] - input_sys.drag_start[0], input_sys.drag_current[1] - input_sys.drag_start[1]))
            rect.normalize()
            pygame.draw.rect(self.window, COLOR_SELECTION, rect, 1)

            # Circular Progress Bar for Castle Build
            if input_sys.hold_timer > 0.1:
                prog = min(1.0, input_sys.hold_timer / CASTLE_CONFIRM_TIME)
                center = input_sys.drag_current
                radius = 20
                
                # Background
                pygame.draw.circle(self.window, (50, 50, 50), center, radius, 4)
                
                # Arc
                # 0 is Right, -PI/2 is Up
                start_angle = -math.pi / 2
                stop_angle = start_angle + (prog * 2 * math.pi)
                
                arc_rect = pygame.Rect(center[0]-radius, center[1]-radius, radius*2, radius*2)
                pygame.draw.arc(self.window, (0, 255, 0), arc_rect, start_angle, stop_angle, 4)

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
             nearby_units = []
             neighbors = self.sm.spatial_hash.query_nearby(target_trans.x, target_trans.y)
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

    def process(self):
        dt = self.sm.dt
        self.timer += dt
        self.expansion_timer += dt

        check_expansion = False
        if self.expansion_timer > 5.0:
            self.expansion_timer = 0
            check_expansion = True

        if self.timer > 0.2:
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
            for ent, (ai, trans, ident) in self.world.get_components(AIController, Transform, Identity):
                if not ai.active: continue
                
                faction = ident.faction
                
                # Expansion Check
                if check_expansion and ai.auto_spawn and faction not in processed_factions:
                    processed_factions.add(faction)
                    self._try_expansion(faction)
                
                # A. Surplus / Defense Spawning
                res = self.sm.resources.get(faction, 0)
                
                # Check damage
                is_damaged = False
                try:
                    stats = self.world.component_for_entity(ent, Stats)
                    if stats.hp < stats.max_hp: is_damaged = True
                except KeyError: pass

                if ai.auto_spawn:
                    # Logic: Spend freely if weak or threatened. Save for expansion if strong.
                    threshold = 100
                    if is_damaged: 
                        threshold = 0
                    elif unit_counts.get(faction, 0) >= 20:
                        threshold = CASTLE_BUILD_COST + 300 # Save up for castle (Cost=500)

                    if res > threshold:
                        # Dump resources
                        while self.sm.resources.get(faction, 0) >= UNIT_COST:
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
                            if t_ident.faction == FACTION_NEUTRAL: priority = 60 # High priority expansion
                            else: priority = 40
                        elif t_ident.type == 'castle': priority = 80 # Ultimate goal
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
