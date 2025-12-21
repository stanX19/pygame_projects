import pygame
import esper
import math
import random
from srcs.config import *
from srcs.components import *
from srcs.spatial_hash import SpatialHash

class CombatSystem(esper.Processor):
    def __init__(self, spatial_hash):
        self.spatial_hash = spatial_hash

    def _find_closest_enemy(self, attacker_ent, attacker_trans, attacker_ident, attacker_stats, ignore_list):
        """
        Find the closest enemy within attack range.
        Returns (enemy_entity_id, distance) or (None, 9999) if no enemy found.
        """
        candidates = self.spatial_hash.query_first_n(
            attacker_trans.x, attacker_trans.y, 
            attacker_stats.attack_range,
            n=5,
            ignore_entity=ignore_list
        )

        closest_enemy = None
        closest_dist = 9999

        for target_id in candidates:
            try:
                t_ident = self.world.component_for_entity(target_id, Identity)
                t_trans = self.world.component_for_entity(target_id, Transform)
                t_stats = self.world.component_for_entity(target_id, Stats)
            except KeyError:
                continue

            # Units can attack enemy units, castles, and neutral resource points
            is_enemy = (t_ident.faction != attacker_ident.faction and t_ident.faction != FACTION_NEUTRAL) or \
                       (t_ident.faction == FACTION_NEUTRAL and t_ident.type == 'resource')
            
            if is_enemy and not t_stats.dead:
                dx = attacker_trans.x - t_trans.x
                dy = attacker_trans.y - t_trans.y
                dist = math.sqrt(dx * dx + dy * dy)

                if dist < attacker_stats.attack_range + t_trans.radius:
                    if dist < closest_dist:
                        closest_dist = dist
                        closest_enemy = target_id

        return closest_enemy, closest_dist

    def process(self):
        dt = self.world.scene_manager.dt

        # Build faction ignore lists AND obstacle list once per frame (cache for reuse)
        faction_ignore_cache = {}
        obstacle_list = []
        
        for ent, ident in self.world.get_component(Identity):
            faction = ident.faction
            if faction not in faction_ignore_cache:
                faction_ignore_cache[faction] = []
            faction_ignore_cache[faction].append(ent)
            
            # Collect obstacles to exclude from combat queries
            if ident.type == 'obstacle':
                obstacle_list.append(ent)

        # Cooldown management & HP Regen
        for ent, stats in self.world.get_component(Stats):
            if stats.current_cd > 0:
                stats.current_cd -= dt
            
            # HP Regeneration
            if stats.hp_regen > 0 and stats.hp < stats.max_hp and not stats.dead:
                old_hp = stats.hp
                stats.hp = min(stats.max_hp, stats.hp + stats.hp_regen * dt)
                
                # Debug print for castle regen
                if int(old_hp) != int(stats.hp):
                    try:
                        ident = self.world.component_for_entity(ent, Identity)
                        # if ident.type == 'castle':
                        #     print(f"Castle {ident.faction[:4]} regen: {old_hp:.1f} -> {stats.hp:.1f}")
                    except KeyError:
                        pass

        # Combat Logic - Units attacking
        for ent, (trans, ident, stats, vel) in self.world.get_components(Transform, Identity, Stats, Velocity):
            if ident.type != 'unit': continue  # Only units have Velocity

            # Use cached ignore list for this faction + global obstacles
            ignore_list = faction_ignore_cache.get(ident.faction, [ent]) + obstacle_list

            # Find closest enemy using utility function
            closest_enemy, closest_dist = self._find_closest_enemy(ent, trans, ident, stats, ignore_list)


            # Attack
            if closest_enemy is not None:
                # Stop moving to fight
                vel.vx *= 0.1
                vel.vy *= 0.1


                if stats.current_cd <= 0:
                    burst_count = 1
                    if stats.attack_cd < 0:
                        burst_count = 1 + int(-stats.attack_cd * dt)

                    enemy_ident = self.world.component_for_entity(closest_enemy, Identity)
                    enemy_stats = self.world.component_for_entity(closest_enemy, Stats)
                    enemy_trans = self.world.component_for_entity(closest_enemy, Transform)
                    
                    for _ in range(burst_count):
                        if enemy_stats.dead:
                            break

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
                        
                        # Check for death and create kill request
                        if enemy_stats.hp <= 0 and not enemy_stats.dead:
                            enemy_stats.dead = True
                            
                            # Create kill request for CleanupSystem to handle
                            self.world.create_entity(
                                KillRequest(
                                    killer_faction=ident.faction,
                                    killed_entity=closest_enemy
                                )
                            )
                    
                    if stats.attack_cd < 0:
                        stats.current_cd = 0
                    else:
                        stats.current_cd = stats.attack_cd

        # Static Defenses (Castles & Resources)
        for ent, (trans, ident, stats) in self.world.get_components(Transform, Identity, Stats):
            if ident.type not in ['castle', 'resource']: continue

            # Use optimized query with ally + obstacle filtering
            if ident.faction == FACTION_NEUTRAL:
                # Neutral: no allies, but still ignore obstacles
                candidates = self.spatial_hash.query_first_n(
                    trans.x, trans.y, stats.attack_range, n=50, ignore_entity=obstacle_list
                )
            else:
                # Factioned: ignore allies + obstacles
                ignore_list = faction_ignore_cache.get(ident.faction, [ent]) + obstacle_list
                candidates = self.spatial_hash.query_first_n(
                    trans.x, trans.y, stats.attack_range, n=50, ignore_entity=ignore_list
                )
            
            enemy_units = []
            
            for target_id in candidates:
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
                burst_count = 1
                if stats.attack_cd < 0:
                    burst_count = 1 + int(-stats.attack_cd * dt)

                for _ in range(burst_count):
                    # Re-filter valid targets in case they died during burst
                    valid_targets = []
                    for u in enemy_units:
                        s = self.world.component_for_entity(u, Stats)
                        if not s.dead:
                            valid_targets.append(u)
                    
                    if not valid_targets:
                        break

                    target = random.choice(valid_targets)
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
                
                if stats.attack_cd < 0:
                    stats.current_cd = 0
                else:
                    stats.current_cd = stats.attack_cd