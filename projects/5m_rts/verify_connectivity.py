import sys
import os

# Adjust path to find modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../srcs')))

import config
from map_generator import TileMapGenerator

def main():
    print("Initializing Map Generator for verification...")
    # Reduce map size slightly for speed if needed, but standard is fine
    cols, rows = config.MAP_COLS, config.MAP_ROWS
    gen = TileMapGenerator(cols, rows)
    
    print(f"Generating map ({cols}x{rows})...")
    castles, resources, obstacles = gen.generate_map(num_players=4, max_attempts=50)
    
    if not castles:
        print("FAILED: Map generation returned None/Empty")
        return
        
    print("\n--- Verifying Connectivity Rule ---")
    
    # Re-run the internal check on the final map
    # We need to reverse-engineer the 'obstacles' set for the internal function
    # The output 'obstacles' is a list of (x,y,type), but internal function expects set of (x,y)
    obstacle_set = set((x,y) for x,y,_ in obstacles)
    
    # We need to restore gen.castles_placed and gen.grid state if it wasn't preserved perfectly
    # generate_map returns placement, but gen object should still have state.
    # Let's verify gen state matches returned data
    if len(gen.castles_placed) != len(castles):
        print("WARNING: Generator state mismatch with return value!")
        # Manually fix generator state
        gen.castles_placed = castles
        # Grid should be fine?
    
    # Manually run _check_min_2_paths
    result = gen._check_min_2_paths(obstacle_set)
    
    if result:
        print("✓ SUCCESS: _check_min_2_paths returned True on generated map.")
    else:
        print("✗ FAILURE: _check_min_2_paths returned False on generated map!")
        print("Reasons:")
        # We can add debug logic here or rely on the fact that if it failed, map generation shouldn't have returned it (unless logic is flawed)
        # Note: generate_map DOES call _check_min_2_paths internally via constraints.
        # So if we got a map, it SHOULD pass.
    
    print(f"Castles: {len(castles)}")
    print("Verification script complete.")

if __name__ == "__main__":
    main()
