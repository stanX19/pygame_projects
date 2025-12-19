"""
Projectile system for handling attack projectiles.
"""
import esper
import pygame
import math
from config import *
from components import *


class ProjectileSystem(esper.Processor):
    """Handles projectile movement and collision"""
    
    def process(self):
        dt = self.world.scene_manager.dt
        
        # Update all projectiles
        to_remove = []
        for ent, (trans, proj, rend) in self.world.get_components(Transform, Projectile, Renderable):
            # Update lifetime
            proj.lifetime += dt
            
            # Check if expired
            if proj.lifetime >= proj.max_lifetime:
                to_remove.append(ent)
                continue
            
            # Calculate direction to target
            dx = proj.target_x - proj.start_x
            dy = proj.target_y - proj.start_y
            distance = math.hypot(dx, dy)
            
            if distance < 0.001:
                to_remove.append(ent)
                continue
            
            # Normalize direction
            dx /= distance
            dy /= distance
            
            # Move projectile
            move_distance = proj.speed * dt
            trans.x += dx * move_distance
            trans.y += dy * move_distance
            
            # Check if reached target
            dist_to_target = math.hypot(trans.x - proj.target_x, trans.y - proj.target_y)
            if dist_to_target < 5:
                # Apply damage if target still exists
                if proj.target_entity is not None:
                    try:
                        target_stats = self.world.component_for_entity(proj.target_entity, Stats)
                        
                        # Apply damage
                        target_stats.hp -= proj.damage
                        
                        # Check for death and create kill request
                        if target_stats.hp <= 0:
                            target_stats.dead = True
                            
                            # Create kill request for CleanupSystem to handle
                            self.world.create_entity(
                                KillRequest(
                                    killer_faction=proj.attacker_faction,
                                    killed_entity=proj.target_entity
                                )
                            )
                    except KeyError:
                        pass  # Target no longer exists
                
                to_remove.append(ent)
        
        # Remove expired projectiles
        for ent in to_remove:
            self.world.delete_entity(ent)
