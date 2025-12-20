import esper
import math
from srcs.config import *
from srcs.components import *


class ResourceSystem(esper.Processor):
    def process(self):
        dt = self.world.scene_manager.dt
        sm = self.world.scene_manager

        # Generate Resources
        for ent, (gen, ident) in self.world.get_components(ResourceGenerator, Identity):
            multiplier = 1.0  # Could add upgrade logic here
            gen.accumulated += gen.rate * multiplier * dt
            if gen.accumulated > gen.max_capacity:
                gen.accumulated = gen.max_capacity

            if ident.faction == FACTION_NEUTRAL: # no place to add for neutral
                continue
            if gen.accumulated < 1.0:
                continue
            amt = int(gen.accumulated)
            sm.resources[ident.faction] += amt
            gen.accumulated -= amt