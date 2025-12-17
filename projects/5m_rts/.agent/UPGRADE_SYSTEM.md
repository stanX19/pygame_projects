# Upgrade System Implementation

## Overview

A comprehensive upgrade system has been added to the 5m War RTS game, allowing players and AI to strategically improve their units, castles, resource points, and special abilities.

## Upgrade Types

### Unit Upgrades
- **HP**: +5 HP per level (max 5 levels) - Increases unit survivability
- **Damage**: +2 damage per level - Increases unit offense
- **Attack Speed**: -0.1s cooldown per level - Faster attacks
- **Movement Speed**: +20 speed per level - Better positioning and mobility

### Castle Upgrades
- **HP**: +100 HP per level - Stronger base defense
- **Damage**: +5 damage per level - Better defensive firepower
- **Attack Speed**: -0.05s cooldown per level - Faster defensive response

### Resource Point Upgrades
- **Generation Rate**: +0.5 resources/sec per level - Faster economy

### Global Upgrades (Per Faction)
- **Castle-to-Castle Movement**: Increases speed multiplier for reinforcements between castles
  - Base: 3x normal speed
  - Upgrade: +0.5x per level

## Cost System

- **Base Cost**: 5 resources for level 1
- **Scaling**: Cost × 1.5^(current_level)
  - Level 1: 5 resources
  - Level 2: 7 resources (rounded)
  - Level 3: 11 resources
  - Level 4: 16 resources
  - Level 5: 25 resources

## AI Upgrade Strategy

The AI makes intelligent upgrade decisions based on game time:

### Early Game (0-90 seconds)
- **Priority**: Offensive power
- Upgrades unit damage first
- Then upgrades unit HP for survivability

### Mid Game (90-180 seconds)
- **Priority**: Defense and mobility
- Upgrades castle HP to defend base
- Improves unit speed for positioning
- Enhances castle damage for better defense

### Late Game (180+ seconds)
- **Priority**: Economic and complete optimization
- Upgrades resource generation if capturing points
- Unlocks castle-to-castle movement for fast reinforcements  
- Maximizes remaining unit upgrades (cheapest first)

### Decision Frequency
- AI checks for upgrades every 10 seconds
- Only upgrades if faction has ≥15 resources (saves for units/expansion)

## Technical Implementation

### New Files
- **`upgrade_system.py`**: UpgradeSystem processor with all upgrade methods
- **`config.py`**: Added upgrade constants and bonuses

### Modified Files
- **`components.py`**: Added `Upgrades` and `FactionUpgrades` components
- **`main.py`**: 
  -  Added `faction_upgrades` tracking dictionary
  - Added `init_faction_upgrades()` method
  - Added `apply_faction_upgrades_to_entity()` method
  - Modified `create_entity()` to apply current faction upgrades
  - Integrated UpgradeSystem into game loop

- **`systems.py`**: 
  - Added `_try_upgrades()` method to AISystem
  - Integrated upgrade checks in AI decision loop

## How It Works

### For Newly Spawned Units
1. When a unit/castle is created, `apply_faction_upgrades_to_entity()` is called
2. Current faction upgrade levels are applied to the entity's stats
3. Entity spawns with all current bonuses already applied

### For Existing Units
1. When an upgrade is purchased, the UpgradeSystem iterates through all existing entities
2. Updates their `Upgrades` component levels
3. Recalculates and applies new stats based on upgrade levels

### Upgrade Bonuses Are Additive
- HP bonuses add to max HP and scale current HP proportionally
- Damage bonuses directly increase attack damage
- Cooldown bonuses reduce attack cooldown (minimum 0.1s)
- Speed bonuses increase movement speed

## Player Upgrade UI (To Be Implemented)

The foundation is ready for player upgrade controls. Future UI will need to:
- Show current upgrade levels for each category
- Display costs for next level
- Provide buttons to purchase upgrades
- Show faction resource count

Access upgrade functions via:
```python
upgrade_sys = world.get_processor(UpgradeSystem)
success = upgrade_sys.upgrade_unit_hp(FACTION_PLAYER)
```

## Testing

To test upgrades:
1. Run the game
2. AI will automatically purchase upgrades based on strategy
3. Observe increased unit/castle effectiveness over time
4. Check console/debug output for upgrade purchases (if added)

## Balance Notes

- Upgrades provide significant power spikes
- AI resource management balances unit production vs upgrades
- Early damage upgrades can snowball advantages
- Late-game economy upgrades help catch up
- Castle HP upgrades make bases much harder to take
