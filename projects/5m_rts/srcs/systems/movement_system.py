import pygame
import esper
import math
import random
from srcs.config import *
from srcs.components import *
from srcs.spatial_hash import SpatialHash





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