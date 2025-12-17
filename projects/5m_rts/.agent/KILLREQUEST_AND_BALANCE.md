# Architecture Refactor: KillRequest System & Range Upgrade Balance

## ✅ Completed Changes

### 1. Decoupled Death/Capture Logic

**Problem**: Death and capture mechanics were scattered across CombatSystem and ProjectileSystem, leading to code duplication and maintenance issues.

**Solution**: Introduced KillRequest component and CleanupSystem for centralized death handling.

#### New Components
- **`KillRequest`** - Stores killer_faction and killed_entity for processing

#### New System
- **`CleanupSystem`** - Processes all kill requests and handles:
  - **Units**: Delete entity
  - **Resource Points**: Capture (change faction, restore HP, update color)
  - **Castles**: Capture (change faction, restore HP, update color, update AI)

#### Modified Systems
- **`CombatSystem`** - Now only applies damage and creates KillRequest on death
- **`ProjectileSystem`** - Now only applies damage and creates KillRequest on death

#### Benefits
- **Single Responsibility**: Each system has one job
- **No Code Duplication**: Death logic exists in one place
- **Easier to Maintain**: Changes to capture mechanics happen in one file
- **Better Architecture**: Follows ECS principles more closely

### 2. Range Upgrade Balance (5x Cost)

**Problem**: Range upgrade was overpowered - turning melee units into ranged attackers for cheap.

**Solution**: Made range upgrades 5x more expensive than other upgrades.

#### Cost Progression

**Normal Upgrades** (HP, DMG, CD, Speed):
- Level 1: 5 resources
- Level 2: 7 resources
- Level 3: 11 resources
- Level 4: 16 resources
- Level 5: 25 resources

**Range Upgrade** (5x multiplier):
- Level 1: **25 resources** ⚠️
- Level 2: **37 resources** ⚠️
- Level 3: **56 resources** ⚠️
- Level 4: **83 resources** ⚠️
- Level 5: **125 resources** ⚠️

#### Implementation
- Added `get_range_upgrade_cost()` static method
- Updated `upgrade_unit_range()` to use expensive cost function
- Updated UI to display correct cost for range upgrades

## File Changes

### New Files
1. **`cleanup_system.py`** - CleanupSystem processor
2. **`components.py`** - Added KillRequest component

### Modified Files
1. **`systems.py`** - Simplified CombatSystem, updated UI cost display
2. **`projectile_system.py`** - Simplified to only damage + create KillRequest
3. **`upgrade_system.py`** - Added get_range_upgrade_cost(), updated upgrade_unit_range()
4. **`main.py`** - Added CleanupSystem to processor list (runs after combat/projectiles)
5. **`config.py`** - User changed STARTING_RESOURCES from 5 to 10

## System Order

Critical that CleanupSystem runs AFTER combat systems:
```python
CombatSystem()       # Creates KillRequests
ProjectileSystem()   # Creates KillRequests  
CleanupSystem()      # Processes KillRequests
```

## Testing

- Range upgrades now cost 25, 37, 56, 83, 125 (vs 5, 7, 11, 16, 25)
- Death mechanics work identically but cleaner code
- Capture mechanics centralized in one place
- No functional changes to gameplay (except range cost)

## Balance Impact

Range upgrades are now a **strategic late-game investment** rather than an easy power spike. Players must carefully consider:
- Should I save 25 resources for range L1, or buy 5 units?
- Is transforming to ranged worth the massive cost?
- Late game with 100+ resources: Still worth it for kiting/siege

This makes range upgrades feel more like a  "game-changing" tech rather than a routine upgrade.
