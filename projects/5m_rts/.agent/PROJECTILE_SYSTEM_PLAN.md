# Attack Range & Projectile System - Implementation Summary

## What Was Added

### 1. New Components (`components.py`)
- **`Projectile`** component for visual attack animations
  - Stores start/target positions, speed, damage, lifetime
- **`range_level`** added to `Upgrades` component

### 2. New Config Constants (`config.py`)
- **`UNIT_RANGE_BONUS = 30`** - +30 range per upgrade level

### 3. New System (`projectile_system.py`)
- **`ProjectileSystem`** - Handles projectile movement and collision
  - Moves projectiles toward targets
  - Applies damage on impact
  - Removes expired projectiles

## What Needs to Be Integrated

### In `main.py`:
1. Import `Projectile` and `ProjectileSystem`
2. Add ProjectileSystem to processor list
3. Create `spawn_projectile()` method:
   ```python
   def spawn_projectile(self, from_x, from_y, to_x, to_y, damage, target_ent, color):
       # Create projectile entity
   ```

### In `systems.py` - CombatSystem:
1. Modify attack logic to check if attack is ranged (range > 20)
2. For ranged attacks: spawn projectile instead of instant damage
3. For melee attacks: keep instant damage

### In `systems.py` - RenderSystem:
1. Render projectiles as small colored circles
2. Layer 2 (above units)

### In `upgrade_system.py`:
1. Add `upgrade_unit_range()` method
2. Apply range bonuses to units

### Visual Design:
- Projectiles: Small (radius 3) colored circles
- Speed: 500 pixels/second
- Color matches attacker faction
- Fade/disappear on impact

## Attack Range Mechanics

**Base Ranges:**
- Units: 15.0
- Castles: 120.0

**Ranged vs Melee:**
- Range > 20: Ranged (spawn projectile)
- Range <= 20: Melee (instant damage)

**Upgrades:**
- Each level adds +30 range
- Level 5 unit: 15 + (30 * 5) = 165 range

This creates interesting gameplay where upgrading range makes units more effective at kiting and siege.
