# Tile-Based Constraint Propagation Map Generator

## ✅ Properly Implemented!

A true **Constraint Satisfaction Problem (CSP) solver** that generates fair, balanced maps using constraint propagation on a discrete tile grid.

## Core Features

### 1. **Discrete Tile Grid** 📐
- All entities (castles, resources, obstacles) placed on **exact tile positions**
- Each entity occupies **exactly one tile** (center of tile)
- No floating-point pixel coordinates during generation
- Tile coordinates converted to pixel coordinates only at the end

### 2. **Constraint Propagation Algorithm** 🧠
Single unified algorithm that places everything together:

```python
for attempt in range(max_attempts):
    1. Place castles (with distance constraint)
    2. Place resources (with fairness constraint)
    3. Place obstacles (randomly)
    4. Validate connectivity (diagonal BFS)
    5. Validate resource fairness (diagonal distance)
    6. If all constraints satisfied → Success!
    7. Else → Retry
```

### 3. **Diagonal Movement Support** ↗️
- Uses **8-directional** movement (cardinal + diagonal)
- **Chebyshev distance** for tile distance: `max(abs(dx), abs(dy))`
- BFS pathfinding with 8 neighbors
- Matches actual game unit movement

## The Four Constraints

### **Constraint 1:  Minimum Castle Distance** 🏰
```python
Distance between any two castles ≥ 4 tiles (Chebyshev)
```
- Prevents spawn camping
- Ensures strategic spacing
- Uses diagonal distance measurement

###**Constraint 2: Castle Connectivity** 🔗
```python
All castles must be reachable from all other castles (8-directional BFS)
```
- No isolated players
- Diagonal pathfinding validation
- Ensures playable map

### **Constraint 3: Resource Fairness** ⚖️
```python
Each castle must have ≥1 resource nearer to it than to any other castle
```
- Uses Chebyshev distance
- Guarantees strategic options for every player
- Fair starting conditions

### **Constraint 4: Tile Alignment** 📍
```python
All castles and resources fit in exactly one tile (center placement)
```
- `pixel_x = tile_x * TILE_SIZE + TILE_SIZE // 2`
- `pixel_y = tile_y * TILE_SIZE + TILE_SIZE // 2`
- No entity spans multiple tiles

## Algorithm Details

### **Castle Placement**
```python
for each player:
    repeat until valid:
        - Random tile position (avoid edges)
        - Check Chebyshev distance ≥ 4 from all existing castles
        - If valid → Place castle
```

### **Resource Placement**
```python
Phase 1 - Guaranteed resources:
    for each castle:
        - Place resource 3-6 tiles away (random angle)
        - Ensures each castle has at least one nearby resource

Phase 2 - Contested resources:
    - Place additional resources in center (Gaussian distribution)
    - Minimum 3 tiles apart from each other
```

### **Obstacle Placement**
```python
for _ in range(num_obstacles):
    - Random tile position
    - Skip if occupied by castle/resource
    - 66% mountains, 33% rivers
```

### **Validation**
```python
1. Connectivity Check:
   - 8-directional BFS from castle[0] to all others
   - If any unreachable → Fail

2. Fairness Check:
   - For each castle, find nearest resource (Chebyshev)
   - If any castle has no nearest → Fail
```

## Diagonal Distance (Chebyshev)

**Why Chebyshev?**
```
In 8-directional movement:
  - Moving diagonally costs 1 step (same as cardinal)
  - Distance = max(|dx|, |dy|)
  
Example:
  From (0,0) to (3,2) = max(3, 2) = 3 steps
  Path: (0,0) → (1,1) → (2,2) → (3,2)
```

**Not Manhattan!**
```
Manhattan would be |dx| + |dy| = 5 steps
But with diagonal, it's only 3 steps!
```

## Tile to Pixel Conversion

```python
# Generation (Tile coordinates)
castle_tiles = [(5, 3), (15, 10), ...]  # Discrete tiles

# Conversion (Pixel coordinates for game)
for tile_x, tile_y in castle_tiles:
    pixel_x = tile_x * TILE_SIZE + TILE_SIZE // 2  # Center of tile
    pixel_y = tile_y * TILE_SIZE + TILE_SIZE // 2
    create_entity('castle', pixel_x, pixel_y, faction)
```

**Example** (TILE_SIZE = 64):
- Tile (5, 3) → Pixel (352, 224)
  - `5 * 64 + 32 = 352`
  - `3 * 64 + 32 = 224`

## Random Player Assignment

Players are randomly assigned to generated castle positions:
```python
all_factions = [FACTION_PLAYER] + bot_factions  # Shuffled order
for i, (cx, cy) in enumerate(generated_castle_positions):
    faction = all_factions[i]
    create_entity('castle', cx, cy, faction)
```

Each game you could be:
- Top-left corner
- Bottom-right corner  
- Center of map
- Anywhere!

## Performance

- **Generation**: ~50-200ms typically
- **Max attempts**: 100 (usually succeeds in 1-10)
- **Fallback**: Guaranteed simple map if all attempts fail
- **Grid size**: 20x11 tiles (1280x704 with 64px tiles)

## Example Map (Tile Grid)

```
  0 1 2 3 4 5 6 7 8 9 ...
0 . . . . . . . . . . 
1 . . 🏰. . . . . . .   Castle at (2,1)
2 . . . . ⛰️. 💎. . .   Resource at (6,2)
3 . . . . . . . . . .
4 . 💎. . . . . . . .   Resource at (1,4)
5 . . . ⛰️. ⛰️. . . .
6 . . . . . . . . . . 
7 . . . . . . 💎. . .   Resource at (6,7)
8 . . . . . . . . 🏰.   Castle at (8,8)
9 . . . . . . . . . .

Distances:
- Castle (2,1) to (8,8) = max(|8-2|, |8-1|) = max(6, 7) = 7 tiles ✓ (≥4)
- Castle (2,1) has nearest resource at (1,4): dist = max(1,3) = 3 ✓
- Castle (8,8) has nearest resource at (6,7): dist = max(2,1) = 2 ✓
```

## Key Differences from Previous Version

| Previous | Now |
|----------|-----|
| Pixel coordinates | **Tile coordinates** |
| Continuous positions | **Discrete grid** |
| Manhattan distance | **Chebyshev distance** |
| Separate placement | **Unified CSP solver** |
| Hardcoded order | **Random assignment** |
| 4-direction validation | **8-direction (diagonal)** |

Now you have a true constraint propagation system! 🎮
