import pygame
import random
from config import *

# C-code definitions adapted
TILE_PATH = 1
TILE_WALL = 2
TILE_WATER = 4

class BackgroundGenerator:
    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows
        # Assets
        self.tiles = {
            'water_path': [], # Row 0
            'path_wall': [],  # Row 1
            'all_grass': []   # Row 2
        }
        self.load_assets()

    def load_assets(self):
        """Load and split the background tileset."""
        try:
            # Assuming 16px sprites in the tileset for 4x scaling
            # The tileset is 256x64.
            # 256 / 16 = 16 sprites per row
            # 64 / 16 = 4 rows
            img = pygame.image.load('sprites/tilesets/background.png').convert_alpha()
            
            sprite_size = 16
            
            # Helper to extract a row of sprites
            def get_row(row_idx):
                sprites = []
                for x in range(16): # 16 sprites per row
                    rect = pygame.Rect(x * sprite_size, row_idx * sprite_size, sprite_size, sprite_size)
                    sprites.append(img.subsurface(rect))
                return sprites

            self.tiles['path_wall'] = get_row(2)
            self.tiles['water_path'] = get_row(1)
            self.tiles['all_grass'] = get_row(3)
            
            print("Background assets loaded successfully.")
            
        except Exception as e:
            print(f"Failed to load background assets: {e}")
            # Create fallback colored squares if loading fails
            surface = pygame.Surface((16, 16))
            surface.fill((30, 100, 30))
            fallback = [surface] * 16
            self.tiles['water_path'] = fallback
            self.tiles['path_wall'] = fallback
            self.tiles['all_grass'] = fallback

    def get_tile_flags(self, tile_type):
        """Map map generator strings to binary flags."""
        if tile_type in ['river', 'river_vertical', 'river_horizontal']:
            return TILE_WATER
        elif tile_type in ['hill', 'hill_center', 'mountain']:
            # Treat hills as walls for visual distinctness if desired, 
            # or just map them to WALL logic
            return TILE_WALL
        else:
            # Empty, fieldland, castle, resource -> Path/Grass
            return TILE_PATH

    def get_corres_sprite(self, c):
        """
        Determine which sprite to use based on 4 corner flags.
        c is a list/array of 4 flags: [TL, TR, BL, BR]
        """
        # Logic from C code:
        # val = ((c[0] | c[1] | c[2] | c[3]) & (TILE_PATH | TILE_WALL | TILE_WATER));
        val = (c[0] | c[1] | c[2] | c[3]) & (TILE_PATH | TILE_WALL | TILE_WATER)
        
        type_sprites = self.tiles['water_path']
        
        # Adaptation of conditional logic
        if val == (TILE_PATH | TILE_WALL) or val == TILE_PATH or val == TILE_WALL:
            type_sprites = self.tiles['path_wall']
            # map_equal_to(c, TILE_WALL) -> Set flag to 1 if it matches TILE_WALL, else 0
            # But the C code does: c[i] = ((c[i] & val) == val)
            # Wait, the C function `map_equal_to(c, val)` basically effectively treats 
            # anything that HAS the bit as 1, and others as 0?
            # actually looking closer at C code:
            # c[0] = ((c[0] & val) == val); -> This results in 0 or 1.
            # Because standard C boolean is integer 0 or 1.
            
            # Effectively, checks if TILE_WALL bit is present.
            target_val = TILE_WALL
            c = [1 if (x & target_val) == target_val else 0 for x in c]
            
        elif val == (TILE_PATH | TILE_WATER) or (val & TILE_WATER):
            type_sprites = self.tiles['water_path']
            # map_not_equal_to(c, TILE_WATER);
            # c[0] = (c[0] != val);
            # Logic: If it IS water, it becomes 0. If it IS NOT water, it becomes 1.
            # So Water=0, Land=1.
            target_val = TILE_WATER
            c = [1 if x != target_val else 0 for x in c]
        
        else:
            # Default case logic from C?
            # The C code handled path/wall and path/water. 
            # If complex mix (Water + Wall?), it might default loop fallback
            # For now stick to strict translation.
            pass

        # Calculate bitmask index: val = binary_4bit(c[0], c[1], c[2], c[3])
        # Return ((num4 << 3) | (num3 << 2) | (num2 << 1) | (num1));
        # c index: 0=TL, 1=TR, 2=BL, 3=BR ?
        # C code: 
        # c[0] = grid[y][x]
        # c[1] = grid[y][x+1] ...
        # So 0=TL, 1=TR, 2=BL, 3=BR
        
        # binary_4bit arg order in C call: c[0], c[1], c[2], c[3] -> num4, num3, num2, num1
        # Implementation: num4<<3 (8), num3<<2 (4), num2<<1 (2), num1(1)
        # So TL is MSB? No.
        # c[0] passed as num4.
        
        idx = (c[0] << 3) | (c[1] << 2) | (c[2] << 1) | (c[3])
        
        # Random variation logic from C
        # if ((type == path_wall && val == 0) || (type == water_path && val == 15)) ...
        # val here is the index (0-15)
        
        # Determine if we are "fully" something
        is_full_grass = False
        
        if (type_sprites == self.tiles['path_wall'] and idx == 0): 
            # Path/Wall set check against Wall. 
            # We mapped Wall=1. So idx=0 means all 4 corners are NOT Wall -> All Path.
            is_full_grass = True
            
        elif (type_sprites == self.tiles['water_path'] and idx == 15):
            # Water/Path set check against Water.
            # We mapped Water=0, Path=1. 
            # So idx=15 means all 4 corners are Path (1,1,1,1).
            is_full_grass = True
            
        if is_full_grass:
            type_sprites = self.tiles['all_grass']
            # val = (rand() % 4 == 0) * rand() % 16;
            # 25% chance of variation, else 0 (default grass)
            if random.random() < 0.25:
                idx = random.randint(0, 15)
            else:
                idx = 0
                
        return type_sprites[idx % 16]

    def generate(self, grid_data):
        """
        Generate the background image.
        grid_data: 2D array of tile types (strings).
        """
        # Map pixels: cols * TILE_SIZE, rows * TILE_SIZE
        # TILE_SIZE is 64.
        # We are building this from 16x16 subtiles.
        # 64 / 16 = 4 subtiles per map tile.
        
        width_px = self.cols * TILE_SIZE
        height_px = self.rows * TILE_SIZE
        
        surface = pygame.Surface((width_px, height_px))
        
        # We go row by row in SUBTILES (4x resolution of grid)
        # Using [edge, tile, tile, tile, edge, tile...] pattern requested
        
        # Actually, let's look at the pattern requirement again:
        # "do [edge, tile, tile, tile, edge, tile, tile, tile, edge, ..., edge, tile]"
        # This implies we sample the grid at specific offsets.
        
        # 64px tile = 4 subtiles (0, 1, 2, 3)
        # Subtile 0 (Top-Left 16x16): influenced by Top-Left neighbor?
        # The C code: get_tile_size(x) -> x*2 - 1.
        # It generated 2x-1 subtiles? 
        # Ah, in C code it was matching edges.
        
        # Let's simplify and follow the User's "Catch" instruction:
        # "we are 64px so you need to do [edge, tile, tile, tile, edge, tile, tile, tile, edge, ..., edge, tile]"
        
        # This means for a tile at grid x,y:
        # We produce 4x4 subtiles.
        # Subtile x=0: Edge transition from Left Neighbor
        # Subtile x=1,2,3: Pure Center (or transition to Right if it's the last one? No, right edge is x=0 of next)
        
        # Actually, if we do [edge, tile, tile, tile], that is 4 subtiles.
        # Edge (0): Spans transition from (x-1) to (x).
        # Inner (1,2,3): Pure (x).
        
        # But auto-tiling usually defines "Corners".
        # Let's use coordinate logic.
        # We iterate through Subtiles (sx, sy).
        
        sub_rows = self.rows * 4
        sub_cols = self.cols * 4
        
        # Pre-convert grid to flags for speed
        flag_grid = [[self.get_tile_flags(t) for t in row] for row in grid_data]
        
        # Extend range by 1 to cover the gap from the -8 shift
        for sy in range(sub_rows + 1):
            for sx in range(sub_cols + 1):
                # Map subtile to Grid Coordinate
                gx = sx // 4
                gy = sy // 4
                
                # Determine "Phase" (0, 1, 2, 3) within the tile
                px = sx % 4
                py = sy % 4
                
                # Logic: Is this an edge subtile?
                # User says: [edge, tile, tile, tile]
                # So if px==0 or py==0?
                # Let's check neighbors based on this.
                
                # Corner Sampling:
                # We need 4 samples for the 4 corners of the SUBTILE.
                # A Subtile at (sx, sy) covers a small area.
                # Samples correspond to top-left, top-right, bottom-left, bottom-right of THIS 16x16 block.
                
                # "Edge" usually implies mixing. "Tile" implies pure.
                # If px=0 (Left Edge of tile gx), the Left corners of this subtile should sample (gx-1), 
                # and Right corners sample (gx).
                
                # If px=1,2,3: Both Left and Right corners sample (gx).
                
                # Let's generalize:
                # Sample TL: (gx, gy) shifted?
                
                # Helper to sample grid with bounds check
                def get_flag(x, y):
                    if 0 <= x < self.cols and 0 <= y < self.rows:
                        return flag_grid[y][x]
                    # Out of bounds default? 
                    # If x < 0, use x=0? or default to something?
                    # Usually void is WATER or WALL or EMPTY?
                    # Let's clamp.
                    cx = max(0, min(x, self.cols - 1))
                    cy = max(0, min(y, self.rows - 1))
                    return flag_grid[cy][cx]

                # Deriving the Logic from "Edge, Tile, Tile, Tile":
                # Offset mapping for the 4 corners of the subtile
                # 0 = Left/Top edge, 1..3 = Center
                
                # TL Corner of subtile:
                # If px=0: Mix with Left (x-1) -> Actually, center of sample is on the edge.
                # Let's define the "Source Tile" for the 4 corners of the subtile.
                
                # If px == 0: Left corners = gx-1, Right corners = gx
                # If px > 0:  Left corners = gx,   Right corners = gx
                
                # Same for Y.
                
                # TL sample:
                tl_gx = gx - 1 if px == 0 else gx
                tl_gy = gy - 1 if py == 0 else gy
                
                # TR sample:
                tr_gx = gx # Always gx because even at px=0, right side is in gx.
                tr_gy = gy - 1 if py == 0 else gy
                
                # BL sample:
                bl_gx = gx - 1 if px == 0 else gx
                bl_gy = gy # Always gy
                
                # BR sample:
                br_gx = gx
                br_gy = gy
                
                # Get flags
                c = [
                    get_flag(tl_gx, tl_gy), # TL
                    get_flag(tr_gx, tr_gy), # TR
                    get_flag(bl_gx, bl_gy), # BL
                    get_flag(br_gx, br_gy)  # BR
                ]
                
                # Resolve Sprite
                sprite = self.get_corres_sprite(c)
                
                # Blit (Shifted -8 to align center)
                surface.blit(sprite, (sx * 16 - 8, sy * 16 - 8))
                
        return surface

