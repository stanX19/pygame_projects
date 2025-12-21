
import sys
import os
import math
import collections

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from srcs.spatial_hash import SpatialHash

class MockEntity:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y
    
    def __repr__(self):
        return f"Ent({self.id}, {self.x}, {self.y})"

def test_query_first_n():
    sh = SpatialHash(cell_size=10)
    
    # Setup: 
    # Center: (0,0)
    # Ent1 (Ally) at (2,0) - dist 2
    # Ent2 (Enemy) at (3,0) - dist 3
    # Ent3 (Enemy) at (8,0) - dist 8
    
    e1 = MockEntity(1, 2, 0)
    e2 = MockEntity(2, 3, 0)
    e3 = MockEntity(3, 8, 0)
    me = MockEntity(0, 0, 0) # The seeker
    
    sh.insert(e1, e1.x, e1.y, 1)
    sh.insert(e2, e2.x, e2.y, 1)
    sh.insert(e3, e3.x, e3.y, 1)
    
    print("Testing basic query...")
    # Basic query, n=1. Should satisfy with e1 (closest)
    res = sh.query_first_n(0, 0, radius=10, n=1)
    print(f"Result (n=1): {res}")
    assert e1 in res or e2 in res
    
    print("Testing ignore ally...")
    # Ignore e1 (ally)
    res_ignore = sh.query_first_n(0, 0, radius=10, n=1, ignore_entity=[e1])
    print(f"Result (ignore e1): {res_ignore}")
    
    # Should find e2
    assert e1 not in res_ignore
    assert e2 in res_ignore or e3 in res_ignore
    
    print("Testing n=2 with ignore...")
    # Ignore e1, get 2
    res_n2 = sh.query_first_n(0, 0, radius=10, n=2, ignore_entity=[e1])
    print(f"Result (n=2, ignore e1): {res_n2}")
    assert len(res_n2) == 2
    assert e2 in res_n2 and e3 in res_n2
    
    print("Test Passed!")

if __name__ == "__main__":
    try:
        test_query_first_n()
    except Exception as e:
        print(f"Test Failed: {e}")
        import traceback
        traceback.print_exc()
