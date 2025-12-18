
import sys
import os
import config

# Add project root to path
sys.path.append(os.getcwd())

from map_generator import TileMapGenerator

def verify():
    print("Initializing Map Generator...")
    # Use config dimensions interactively or just use what's in config
    gen = TileMapGenerator(config.MAP_COLS, config.MAP_ROWS)
    
    print(f"Generating map for {config.NUM_PLAYERS} players...")
    print(f"Expecting {config.NUM_PLAYERS * config.RESOURCES_PER_CASTLE} guaranteed + {config.EXTRA_RESOURCES} extra = {config.NUM_PLAYERS * config.RESOURCES_PER_CASTLE + config.EXTRA_RESOURCES} resources.")
    
    try:
        castles, resources, obstacles = gen.generate_map(num_players=config.NUM_PLAYERS, max_attempts=10)
    except Exception as e:
        print(f"GENERATION CRASHED: {e}")
        import traceback
        traceback.print_exc()
        return

    if not castles:
        print("FAILED: No map generated (returned None or empty)")
        return

    print("\n--- RESULTS ---")
    print(f"Castles: {len(castles)}")
    print(f"Resources: {len(resources)}")
    
    expected_resources = (config.NUM_PLAYERS * config.RESOURCES_PER_CASTLE) + config.EXTRA_RESOURCES
    if len(resources) == expected_resources:
        print(f"PASS: Resource count matches expected ({expected_resources})")
    else:
        print(f"FAIL: Resource count {len(resources)} != expected {expected_resources}")
        
    # Check guaranteed resources
    print("\nChecking Fairness...")
    for cx, cy in castles:
        nearby = 0
        for rx, ry in resources:
            dist = abs(rx - cx) + abs(ry - cy)
            if dist <= 5: # Assuming 'near' is within 5 tiles path
                nearby += 1
        print(f"Castle at ({cx},{cy}) has {nearby} resources within radius 5")
        if nearby < config.RESOURCES_PER_CASTLE:
             print(f"  WARNING: Castle might be under-supplied (target {config.RESOURCES_PER_CASTLE})")

    # Check extra resources distance
    print("\nChecking Extra Resource Distances...")
    # It's hard to distinguish which is which without logic, but we can check if there are resources far away
    far_resources = 0
    for rx, ry in resources:
        min_dist_to_castle = min(abs(rx - cx) + abs(ry - cy) for cx, cy in castles)
        if min_dist_to_castle >= config.MIN_RESOURCE_DIST:
            far_resources += 1
            
    print(f"Resources >= {config.MIN_RESOURCE_DIST} tiles from any castle: {far_resources}")
    if far_resources < config.EXTRA_RESOURCES:
         print(f"  WARNING: Fewer 'far' resources than EXTRA_RESOURCES ({config.EXTRA_RESOURCES}). Some might have spawned closer or map is small.")
    
    print("\nDone.")

if __name__ == "__main__":
    verify()
