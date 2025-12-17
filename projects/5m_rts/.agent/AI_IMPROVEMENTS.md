# AI Improvements: Expansion & Upgrade Diversity

## ✅ Fixed Issues

### 1. **Castle Building Near Resource Points** 🏰

**Problem**: AI was rallying units directly at resource points to build castles, but you can't build castles at the exact same position (overlap).

**Solution**: When checking for castle-building readiness near resource points, offset the check position by 120 units in a random direction.

```python
if target_ident.type == 'resource':
    # Offset by 120 in a random direction for resource points
    angle = random.uniform(0, 6.28)
    check_x = target_trans.x + math.cos(angle) * 120
    check_y = target_trans.y + math.sin(angle) * 120
```

**Result**: AI now rallies units NEAR resource points (120 units away) instead of directly ON them, allowing successful castle construction.

### 2. **Randomized AI Upgrade Choices** 🎲

**Problem**: All AI factions were upgrading in the exact same order, making them predictable and boring.

**Solution**: Added weighted random selection for all upgrade decisions.

#### Early Game (0-90s)
- **Options**: Unit DMG (weight 3) or Unit HP (weight 2)
- **Random**: Picks based on weighted probability
- **Result**: Some bots rush damage, others prioritize tankiness

#### Mid Game (90-180s)
- **Options**: Castle HP (weight 3), Unit Speed (weight 2), Castle DMG (weight 2)
- **Random**: Equal chance among affordable options
- **Result**: Different defensive vs offensive strategies

#### Late Game (180s+)
- **Previous**: Always picked cheapest upgrade
- **Now**: Randomly picks from ALL affordable upgrades
- **Result**: Diverse upgrade paths - some max HP first, others max speed, etc.

### 3. **User Config Changes** ⚙️
User adjusted these values:
- `UNIT_SPEED`: 120 → 30 (slower base speed)
- `UNIT_SPEED_BONUS`: 20 → 10 (smaller speed upgrade bonus)
- `STARTING_RESOURCES`: 20 → 100 (more starting resources)

## Gameplay Impact

### **Faction Diversity** 🌈
Each AI faction now develops unique characteristics:
- **Faction A**: Heavy HP focus → Tanky blocky units
- **Faction B**: Damage rush → Sharp spiky units  
- **Faction C**: Speed focus → Streamlined teardrop units
- **Faction D**: Range investment → Star-shaped snipers

### **More Interesting Battles** ⚔️
- Different unit types clash with different strategies
- Visual variety - each faction looks different
- Unpredictable AI behavior keeps gameplay fresh

### **Better Expansion** 🏗️
- AI successfully builds castles near resource points
- No more failed castle construction attempts
- Strategic expansion gameplay works as intended

## Technical Details

**Weighted Random Selection**:
```python
upgrade_options.append((type, cost, weight))
total_weight = sum(opt[2] for opt in upgrade_options)
rand = random.uniform(0, total_weight)
# Pick based on cumulative weights
```

**Rally Offset System**:
- Castles: Rally directly at position
- Resources: Rally at position + 120-unit random offset
- Ensures buildable space while still defending points

Now every AI faction plays differently! 🎮
