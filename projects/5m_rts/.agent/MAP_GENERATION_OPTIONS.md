# Procedural Map Generation Options for 5m RTS

## Current State
Your map is hardcoded in `generate_terrain()` - manually placing rivers, mountains, castles, and resources.

## Procedural Generation Algorithms

### 1. **Perlin/Simplex Noise** 🌄
**Best for**: Terrain features (mountains, rivers, elevation)

**How it works**:
- Generates smooth, natural-looking random values
- Creates continuous height maps
- Good for organic-looking terrain

**Implementation**:
```python
from noise import pnoise2  # pip install noise

def generate_terrain_noise(self):
    for x in range(0, SCREEN_WIDTH, TILE_SIZE):
        for y in range(0, SCREEN_HEIGHT, TILE_SIZE):
            noise_val = pnoise2(x/100.0, y/100.0)
            if noise_val > 0.3:  # Mountain
                self.add_tile(x, y, 'mountain')
            elif noise_val < -0.2:  # River
                self.add_tile(x, y, 'river')
```

**Pros**: Natural, organic-looking terrain
**Cons**: Can create imbalanced/unfair maps

---

### 2. **Voronoi Diagrams** 🗺️
**Best for**: Territories, regions, resource clusters

**How it works**:
- Place random seed points
- Each cell belongs to nearest seed
- Creates distinct regions

**Implementation**:
```python
from scipy.spatial import Voronoi

def generate_voronoi_map(self, num_regions=5):
    # Place seed points
    seeds = [(random.randint(0, SCREEN_WIDTH), 
              random.randint(0, SCREEN_HEIGHT)) 
             for _ in range(num_regions)]
    
    # Each region gets different features
    # Region 0: Starting area, Region 1-4: Contested zones
```

**Pros**: Creates balanced territories, symmetrical options
**Cons**: Can look too geometric

---

### 3. **Cellular Automata** 🧬
**Best for**: Caves, organic obstacles, fluid terrain

**How it works**:
- Start with random cells (alive/dead)
- Apply rules: If 4+ neighbors alive, cell becomes alive
- Iterate to create organic shapes

**Implementation**:
```python
def generate_cellular_map(self, iterations=5):
    grid = [[random.random() > 0.5 for _ in range(cols)] 
            for _ in range(rows)]
    
    for _ in range(iterations):
        new_grid = evolve_cellular(grid)  # Apply CA rules
        grid = new_grid
    
    # Convert to obstacles
    for x, y in grid:
        if grid[y][x]:
            self.add_tile(x*TILE_SIZE, y*TILE_SIZE, 'mountain')
```

**Pros**: Natural-looking obstacles, caves
**Cons**: Can block paths, needs validation

---

### 4. **Symmetrical/Mirrored Generation** ⚖️
**Best for**: Fair competitive RTS (like yours!)

**How it works**:
- Generate half the map
- Mirror it for opponent
- Ensures balance

**Implementation**:
```python
def generate_symmetrical_map(self, players=2):
    # Generate left half
    for x in range(0, SCREEN_WIDTH//2):
        if random.random() < 0.1:
            self.add_tile(x, y, 'mountain')
            # Mirror to right
            mirror_x = SCREEN_WIDTH - x
            self.add_tile(mirror_x, y, 'mountain')
```

**Pros**: Perfectly balanced, competitive
**Cons**: Predictable, less variety

---

### 5. **Poisson Disk Sampling** 📍
**Best for**: Resource/castle placement (uniform distribution)

**How it works**:
- Places points with minimum distance between them
- Ensures no clustering or gaps
- Perfect for strategic points

**Implementation**:
```python
def poisson_disk_sampling(width, height, radius, k=30):
    # Returns list of (x, y) points uniformly distributed
    # Minimum distance = radius between points
    pass

# Use for castle placement
positions = poisson_disk_sampling(SCREEN_WIDTH, SCREEN_HEIGHT, 200)
for x, y in positions[:4]:  # 4 castles
    self.create_entity('castle', x, y, factions[i])
```

**Pros**: Even distribution, no unfair clusters
**Cons**: Needs library or complex implementation

---

### 6. **Template-Based** 📋
**Best for**: Controlled variation, guaranteed balance

**How it works**:
- Define templates (patterns)
- Randomize details within template
- Mix and match sections

**Implementation**:
```python
TEMPLATES = {
    'center_mountain': {
        'obstacles': [(640, 360, 'mountain')],  # Center
        'resources': [(200, 200), (1080, 200), (200, 520), (1080, 520)]
    },
    'river_vertical': {
        'obstacles': [(640, y, 'river') for y in range(0, 720, 64)],
        'resources': [...]
    }
}

def generate_from_template(self):
    template = random.choice(list(TEMPLATES.values()))
    # Apply with slight randomization
```

**Pros**: Guaranteed playability, controlled chaos
**Cons**: Less procedural, more design work

---

### 7. **Hybrid: Zones + Noise** 🎲
**Best for**: Best of both worlds

**How it works**:
- Divide map into zones (center, corners, edges)
- Each zone has rules
- Add noise for variation

**Implementation**:
```python
def generate_hybrid_map(self):
    # Zone 1: Center - contested area
    center_zone = Rect(400, 200, 480, 320)
    self.add_contested_zone(center_zone)
    
    # Zone 2: Corners - starting positions
    for corner in [(100, 100), (1180, 100), (100, 620), (1180, 620)]:
        self.add_starting_base(corner)
    
    # Add noise for obstacles
    self.add_noise_obstacles()
```

**Pros**: Balanced + varied, best for RTS
**Cons**: More complex

---

## **Recommendation for Your Game** ⭐

Given your 5-minute RTS with 2-4 players, I recommend:

### **Hybrid: Symmetrical Templates + Poisson Disk**

```python
def generate_balanced_map(self, num_players):
    # 1. Symmetrical starting positions (corners)
    positions = get_symmetrical_positions(num_players)
    for i, pos in enumerate(positions):
        self.create_entity('castle', pos[0], pos[1], factions[i])
    
    # 2. Center contested zone
    center_resources = poisson_disk_sampling(
        center_area, min_distance=150
    )
    for pos in center_resources:
        self.create_entity('resource', pos[0], pos[1], FACTION_NEUTRAL)
    
    # 3. Random obstacles with Perlin noise
    self.add_noise_obstacles(density=0.15)
    
    # 4. Guaranteed paths (validate pathfinding)
    self.ensure_all_bases_connected()
```

**Why**:
- ✅ Balanced (symmetrical starts)
- ✅ Varied (noise obstacles)
- ✅ Fair (Poisson resources)
- ✅ Fast (< 1 second generation)
- ✅ Always playable (validation)

## Next Steps

1. **Simple**: Start with symmetrical templates
2. **Medium**: Add Poisson disk for resources
3. **Advanced**: Add Perlin noise for obstacles
4. **Polish**: Validate connectivity with pathfinding

Want me to implement one of these?
