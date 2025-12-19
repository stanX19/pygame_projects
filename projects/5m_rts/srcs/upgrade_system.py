"""
Upgrade system for applying and managing upgrades.
"""
import esper
import math
from config import *
from components import *


class UpgradeSystem(esper.Processor):
    """
    Handles upgrade calculations and applies bonuses to entities.
    """
    
    def __init__(self, scene_manager):
        self.sm = scene_manager
    
    @staticmethod
    def get_upgrade_cost(current_level):
        """Calculate cost for next upgrade level"""
        if current_level >= MAX_UPGRADE_LEVEL:
            return float('inf')  # Max level reached
        return int(UPGRADE_COST_BASE * (UPGRADE_COST_MULTIPLIER ** current_level))
    
    @staticmethod
    def get_range_upgrade_cost(current_level):
        """Calculate cost for next range upgrade level (5x more expensive)"""
        if current_level >= MAX_UPGRADE_LEVEL:
            return float('inf')  # Max level reached
        return int(UPGRADE_COST_BASE * (UPGRADE_COST_MULTIPLIER ** current_level) * RANGE_UPGRADE_COST_MULTIPLIER)
    
    def update_unit_visual(self, ent, upgrades, trans):
        """Update unit's visual shape based on upgrade levels"""
        from shape_generator import generate_unit_shape
        
        # Generate custom polygon based on upgrade levels
        polygon_points = generate_unit_shape(
            trans.radius,
            upgrades.hp_level,
            upgrades.dmg_level,
            upgrades.cd_level,
            upgrades.speed_level,
            upgrades.range_level
        )
        
        # Update renderable
        if self.world.has_component(ent, Renderable):
            rend = self.world.component_for_entity(ent, Renderable)
            rend.shape = 'polygon'
            rend.polygon_points = polygon_points
    
    def upgrade_unit_hp(self, faction_id):
        """Upgrade HP for all units of a faction"""
        cost = self.get_upgrade_cost(self.sm.faction_upgrades[faction_id]['unit_hp'])
        if self.sm.resources.get(faction_id, 0) < cost:
            return False
        
        # Deduct cost
        self.sm.resources[faction_id] -= cost
        
        # Upgrade level
        self.sm.faction_upgrades[faction_id]['unit_hp'] += 1
        level = self.sm.faction_upgrades[faction_id]['unit_hp']
        
        # Apply to all existing units
        for ent, (ident, stats, upgrades, trans) in self.world.get_components(Identity, Stats, Upgrades, Transform):
            if ident.faction == faction_id and ident.type == 'unit':
                upgrades.hp_level = level
                # Increase max HP and current HP
                bonus = UNIT_HP_BONUS * level
                new_max_hp = UNIT_HP + bonus
                hp_ratio = stats.hp / stats.max_hp
                stats.max_hp = new_max_hp
                stats.hp = int(new_max_hp * hp_ratio)  # Scale current HP proportionally
                # Update visual shape
                self.update_unit_visual(ent, upgrades, trans)
        
        return True
    
    def upgrade_unit_dmg(self, faction_id):
        """Upgrade damage for all units of a faction"""
        cost = self.get_upgrade_cost(self.sm.faction_upgrades[faction_id]['unit_dmg'])
        if self.sm.resources.get(faction_id, 0) < cost:
            return False
        
        self.sm.resources[faction_id] -= cost
        self.sm.faction_upgrades[faction_id]['unit_dmg'] += 1
        level = self.sm.faction_upgrades[faction_id]['unit_dmg']
        
        for ent, (ident, stats, upgrades, trans) in self.world.get_components(Identity, Stats, Upgrades, Transform):
            if ident.faction == faction_id and ident.type == 'unit':
                upgrades.dmg_level = level
                stats.attack_dmg = UNIT_DMG + (UNIT_DMG_BONUS * level)
                # Update visual shape
                self.update_unit_visual(ent, upgrades, trans)
        
        return True
    
    def upgrade_unit_cd(self, faction_id):
        """Upgrade attack cooldown (reduce) for all units of a faction"""
        cost = self.get_upgrade_cost(self.sm.faction_upgrades[faction_id]['unit_cd'])
        if self.sm.resources.get(faction_id, 0) < cost:
            return False
        
        self.sm.resources[faction_id] -= cost
        self.sm.faction_upgrades[faction_id]['unit_cd'] += 1
        level = self.sm.faction_upgrades[faction_id]['unit_cd']
        
        for ent, (ident, stats, upgrades, trans) in self.world.get_components(Identity, Stats, Upgrades, Transform):
            if ident.faction == faction_id and ident.type == 'unit':
                upgrades.cd_level = level
                stats.attack_cd = max(0.1, UNIT_CD + (UNIT_CD_BONUS * level))
                # Update visual shape
                self.update_unit_visual(ent, upgrades, trans)
        
        return True
    
    def upgrade_unit_speed(self, faction_id):
        """Upgrade movement speed for all units of a faction"""
        cost = self.get_upgrade_cost(self.sm.faction_upgrades[faction_id]['unit_speed'])
        if self.sm.resources.get(faction_id, 0) < cost:
            return False
        
        self.sm.resources[faction_id] -= cost
        self.sm.faction_upgrades[faction_id]['unit_speed'] += 1
        level = self.sm.faction_upgrades[faction_id]['unit_speed']
        
        for ent, (ident, mov, upgrades, trans) in self.world.get_components(Identity, Movement, Upgrades, Transform):
            if ident.faction == faction_id and ident.type == 'unit':
                upgrades.speed_level = level
                mov.speed = UNIT_SPEED + (UNIT_SPEED_BONUS * level)
                # Update visual shape
                self.update_unit_visual(ent, upgrades, trans)
        
        return True
    
    def upgrade_unit_range(self, faction_id):
        """Upgrade attack range for all units of a faction"""
        cost = self.get_range_upgrade_cost(self.sm.faction_upgrades[faction_id]['unit_range'])
        if self.sm.resources.get(faction_id, 0) < cost:
            return False
        
        self.sm.resources[faction_id] -= cost
        self.sm.faction_upgrades[faction_id]['unit_range'] += 1
        level = self.sm.faction_upgrades[faction_id]['unit_range']
        
        for ent, (ident, stats, upgrades, trans) in self.world.get_components(Identity, Stats, Upgrades, Transform):
            if ident.faction == faction_id and ident.type == 'unit':
                upgrades.range_level = level
                stats.attack_range = 15.0 + (UNIT_RANGE_BONUS * level)
                # Update visual shape
                self.update_unit_visual(ent, upgrades, trans)
        
        return True
    
    def upgrade_castle_hp(self, faction_id):
        """Upgrade HP for all castles of a faction"""
        cost = self.get_upgrade_cost(self.sm.faction_upgrades[faction_id]['castle_hp'])
        if self.sm.resources.get(faction_id, 0) < cost:
            return False
        
        self.sm.resources[faction_id] -= cost
        self.sm.faction_upgrades[faction_id]['castle_hp'] += 1
        level = self.sm.faction_upgrades[faction_id]['castle_hp']
        
        for ent, (ident, stats, upgrades) in self.world.get_components(Identity, Stats, Upgrades):
            if ident.faction == faction_id and ident.type == 'castle':
                upgrades.hp_level = level
                bonus = CASTLE_HP_BONUS * level
                new_max_hp = CASTLE_HP + bonus
                hp_ratio = stats.hp / stats.max_hp
                stats.max_hp = new_max_hp
                stats.hp = int(new_max_hp * hp_ratio)
        
        return True
    
    def upgrade_castle_dmg(self, faction_id):
        """Upgrade damage for all castles of a faction"""
        cost = self.get_upgrade_cost(self.sm.faction_upgrades[faction_id]['castle_dmg'])
        if self.sm.resources.get(faction_id, 0) < cost:
            return False
        
        self.sm.resources[faction_id] -= cost
        self.sm.faction_upgrades[faction_id]['castle_dmg'] += 1
        level = self.sm.faction_upgrades[faction_id]['castle_dmg']
        
        for ent, (ident, stats, upgrades) in self.world.get_components(Identity, Stats, Upgrades):
            if ident.faction == faction_id and ident.type == 'castle':
                upgrades.dmg_level = level
                stats.attack_dmg = CASTLE_DMG + (CASTLE_DMG_BONUS * level)
        
        return True
    
    def upgrade_castle_cd(self, faction_id):
        """Upgrade attack cooldown (reduce) for all castles of a faction"""
        cost = self.get_upgrade_cost(self.sm.faction_upgrades[faction_id]['castle_cd'])
        if self.sm.resources.get(faction_id, 0) < cost:
            return False
        
        self.sm.resources[faction_id] -= cost
        self.sm.faction_upgrades[faction_id]['castle_cd'] += 1
        level = self.sm.faction_upgrades[faction_id]['castle_cd']
        
        for ent, (ident, stats, upgrades) in self.world.get_components(Identity, Stats, Upgrades):
            if ident.faction == faction_id and ident.type == 'castle':
                upgrades.cd_level = level
                stats.attack_cd = max(0.1, CASTLE_CD + (CASTLE_CD_BONUS * level))
        
        return True
    
    def upgrade_resource_rate(self, faction_id):
        """Upgrade resource generation rate for all resource points of a faction"""
        cost = self.get_upgrade_cost(self.sm.faction_upgrades[faction_id]['resource_rate'])
        if self.sm.resources.get(faction_id, 0) < cost:
            return False
        
        self.sm.resources[faction_id] -= cost
        self.sm.faction_upgrades[faction_id]['resource_rate'] += 1
        level = self.sm.faction_upgrades[faction_id]['resource_rate']
        
        for ent, (ident, gen, upgrades) in self.world.get_components(Identity, ResourceGenerator, Upgrades):
            if ident.faction == faction_id and (ident.type == 'resource' or ident.type == 'castle'):
                upgrades.rate_level = level
                gen.rate = RES_GENERATION_RATE + (RESOURCE_RATE_BONUS * level)
        
        return True
    
    def upgrade_castle_move(self, faction_id):
        """Upgrade castle-to-castle movement speed (global for faction)"""
        cost = self.get_upgrade_cost(self.sm.faction_upgrades[faction_id]['castle_move'])
        if self.sm.resources.get(faction_id, 0) < cost:
            return False
        
        self.sm.resources[faction_id] -= cost
        self.sm.faction_upgrades[faction_id]['castle_move'] += 1
        
        return True
    
    def get_castle_move_multiplier(self, faction_id):
        """Get the current castle-to-castle movement speed multiplier for a faction"""
        level = self.sm.faction_upgrades[faction_id]['castle_move']
        return CASTLE_MOVE_SPEED_MULTIPLIER + (CASTLE_MOVE_UPGRADE_BONUS * level)
    
    def process(self):
        """
        This system doesn't run every frame - it's called when upgrades are purchased.
        However, we need to ensure newly spawned units get the current upgrade levels.
        """
        pass
