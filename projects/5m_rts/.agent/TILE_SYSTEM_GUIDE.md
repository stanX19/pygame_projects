# Tile System Reference Guide

## Using add_tile()

### Basic Usage

```python
# Add a mountain at tile coordinates (5, 3)
entity_id = scene.add_tile('mountain', tile_x=5, tile_y=3)

# Add a river at tile coordinates (10, 5)
entity_id = scene.add_tile('river', 10, 5)

# Add a resource point
entity_id = scene.add_tile('resource_point', 8, 6)
```

### Coordinate System

**Tile Coordinates:**
- Origin (0, 0) is top-left corner
- X increases to the right (0 to 19 for 1280px wide screen)
- Y increases downward (0 to 11 for 720px tall screen)
- Each tile is 64x64 pixels

**Conversion:**
- Tile to World: `world_x = tile_x * 64 + 32` (center of tile)
- World to Tile: `tile_x = world_x // 64`

### Grid Dimensions

For default screen size (1280x720) with 64px tiles:
- Columns (cols): 20 tiles (0-19)
- Rows (rows): 12 tiles (0-11)

Access via:
```python
scene.cols  # 20
scene.rows  # 12
```

### Example: Creating a Custom Pattern

```python
# Create a diagonal line of mountains
for i in range(5):
    scene.add_tile('mountain', i, i)

# Create a horizontal river
river_y = 6  # Middle of screen
for x in range(scene.cols):
    scene.add_tile('river', x, river_y)

# Place resource points at corners
scene.add_tile('resource_point', 2, 2)      # Top-left
scene.add_tile('resource_point', 17, 2)     # Top-right
scene.add_tile('resource_point', 2, 9)      # Bottom-left  
scene.add_tile('resource_point', 17, 9)     # Bottom-right
```

### Bounds Checking

The method automatically validates coordinates:
```python
# This will print a warning and return None
bad_tile = scene.add_tile('mountain', 100, 100)  # Out of bounds

# Safe usage with bounds check
if 0 <= x < scene.cols and 0 <= y < scene.rows:
    scene.add_tile('mountain', x, y)
```

### Supported Tile Types

1. **'river'**
   - Blue water obstacle
   - Blocks movement
   - Rendered as square

2. **'mountain'**  
   - Brown terrain obstacle
   - Blocks movement
   - Rendered as triangle

3. **'resource_point'**
   - Gold strategic point
   - Can be captured
   - Generates resources for owner
   - Rendered as triangle

### Return Value

Returns the entity ID if successful, or `None` if:
- Coordinates are out of bounds
- Tile type is unknown

```python
entity = scene.add_tile('mountain', 5, 5)
if entity is not None:
    # Successfully created
    print(f"Created obstacle entity {entity}")
```

## Migration Guide

### Old Way (World Coordinates)
```python
# DON'T DO THIS anymore for tile-based entities
scene.create_entity('mountain', 320, 180, FACTION_NEUTRAL)
scene.mark_obstacle(320, 180, 32)
```

### New Way (Tile Coordinates)
```python
# DO THIS instead
scene.add_tile('mountain', 5, 2)  # Automatically marks obstacle
```

### Benefits
- ✅ Automatic obstacle marking
- ✅ Guaranteed grid alignment
- ✅ Simpler coordinate math
- ✅ Consistent pathfinding behavior
- ✅ Bounds validation included
