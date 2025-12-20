import esper
from srcs.config import *
from srcs.components import *

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