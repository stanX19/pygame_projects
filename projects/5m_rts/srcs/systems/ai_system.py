import esper
import math
import random
from srcs.config import *
from srcs.components import *

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