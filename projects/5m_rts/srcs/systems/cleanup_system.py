"""
Cleanup system for handling entity death and capture mechanics.
"""
import esper
from srcs.config import *
from srcs.components import *


class CleanupSystem(esper.Processor):
    """
    Processes KillRequest components to handle death and capture mechanics.
    This decouples death logic from damage systems.
    """
    
    def process(self):
        # Process all kill requests
        kill_requests = []
        for ent, kill_req in self.world.get_component(KillRequest):
            kill_requests.append((ent, kill_req))
        
        for request_ent, kill_req in kill_requests:
            # Check if target still exists
            if not self.world.entity_exists(kill_req.killed_entity):
                self.world.delete_entity(request_ent)
                continue
            
            try:
                target_ident = self.world.component_for_entity(kill_req.killed_entity, Identity)
                target_stats = self.world.component_for_entity(kill_req.killed_entity, Stats)
                
                # Handle different entity types
                if target_ident.type == 'resource':
                    # Capture resource point - change faction and restore HP
                    target_ident.faction = kill_req.killer_faction
                    target_stats.hp = target_stats.max_hp
                    target_stats.dead = False
                    
                    # Update color to match new faction
                    if self.world.has_component(kill_req.killed_entity, Renderable):
                        render = self.world.component_for_entity(kill_req.killed_entity, Renderable)
                        render.color = self.world.scene_manager.get_faction_color(kill_req.killer_faction)
                    
                    # Add resource generator if not present
                    if not self.world.has_component(kill_req.killed_entity, ResourceGenerator):
                        self.world.add_component(kill_req.killed_entity, ResourceGenerator(rate=RES_GENERATION_RATE))
                        
                    # Apply Faction Upgrades
                    self.world.scene_manager.apply_faction_upgrades_to_entity(kill_req.killed_entity, kill_req.killer_faction, 'resource')
                
                elif target_ident.type == 'castle':
                    # Capture castle - change faction and restore HP
                    target_ident.faction = kill_req.killer_faction
                    target_stats.hp = target_stats.max_hp
                    target_stats.dead = False
                    
                    # Update color to match new faction
                    if self.world.has_component(kill_req.killed_entity, Renderable):
                        render = self.world.component_for_entity(kill_req.killed_entity, Renderable)
                        render.color = self.world.scene_manager.get_faction_color(kill_req.killer_faction)
                    
                    # Apply Faction Upgrades
                    self.world.scene_manager.apply_faction_upgrades_to_entity(kill_req.killed_entity, kill_req.killer_faction, 'castle')

                    # Update AI Controller
                    is_player = (kill_req.killer_faction == self.world.scene_manager.player_faction_id)
                    if self.world.has_component(kill_req.killed_entity, AIController):
                        ai = self.world.component_for_entity(kill_req.killed_entity, AIController)
                        ai.auto_attack = not is_player
                        ai.auto_spawn = not is_player
                    else:
                        self.world.add_component(kill_req.killed_entity, 
                            AIController(auto_spawn=not is_player, auto_attack=not is_player))
                
                elif target_ident.type == 'unit':
                    # Units just die and get deleted
                    self.world.delete_entity(kill_req.killed_entity)
                
            except KeyError:
                pass  # Target entity doesn't have required components
            
            # Remove the kill request
            self.world.delete_entity(request_ent)
