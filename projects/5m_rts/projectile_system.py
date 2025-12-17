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
                        target_ident = self.world.component_for_entity(proj.target_entity, Identity)
                        
                        # Apply damage
                        target_stats.hp -= proj.damage
                        
                        # Handle death
                        if target_stats.hp <= 0:
                            target_stats.dead = True
                            
                            # Handle different entity types
                            if target_ident.type == 'resource':
                                # Capture resource point - change faction and restore HP
                                target_ident.faction = proj.attacker_faction
                                target_stats.hp = target_stats.max_hp
                                target_stats.dead = False
                                
                                # Update color to match new faction
                                if self.world.has_component(proj.target_entity, Renderable):
                                    render = self.world.component_for_entity(proj.target_entity, Renderable)
                                    render.color = self.world.scene_manager.get_faction_color(proj.attacker_faction)
                                
                                # Add resource generator if not present
                                if not self.world.has_component(proj.target_entity, ResourceGenerator):
                                    self.world.add_component(proj.target_entity, ResourceGenerator(rate=RES_GENERATION_RATE))
                            
                            elif target_ident.type == 'castle':
                                # Capture castle - change faction and restore HP
                                target_ident.faction = proj.attacker_faction
                                target_stats.hp = target_stats.max_hp
                                target_stats.dead = False
                                
                                # Update color to match new faction
                                if self.world.has_component(proj.target_entity, Renderable):
                                    render = self.world.component_for_entity(proj.target_entity, Renderable)
                                    render.color = self.world.scene_manager.get_faction_color(proj.attacker_faction)

                                # Update AI Controller
                                is_player = (proj.attacker_faction == self.world.scene_manager.player_faction_id)
                                if self.world.has_component(proj.target_entity, AIController):
                                    ai = self.world.component_for_entity(proj.target_entity, AIController)
                                    ai.auto_attack = not is_player
                                    ai.auto_spawn = not is_player
                                else:
                                    self.world.add_component(proj.target_entity, 
                                        AIController(auto_spawn=not is_player, auto_attack=not is_player))
                            
                            elif target_ident.type == 'unit':
                                # Units just die and get deleted
                                self.world.delete_entity(proj.target_entity)
                            
                    except KeyError:
                        pass  # Target no longer exists
                
                to_remove.append(ent)
        
        # Remove expired projectiles
        for ent in to_remove:
            self.world.delete_entity(ent)
