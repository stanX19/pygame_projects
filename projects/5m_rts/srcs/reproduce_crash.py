from shape_generator import generate_unit_shape

def test_shapes():
    # Test case that previously caused a crash (CD Level 7+)
    # With segments=32, cd_level=7 -> indent_count=33. 32//33 = 0. Error.
    print("Testing CD Level 7 (Crash case)...")
    try:
        generate_unit_shape(10, 0, 0, 7, 0, 0)
        print("Success: CD Level 7 generated.")
    except ZeroDivisionError:
        print("FAIL: CD Level 7 crashed.")
    except Exception as e:
        print(f"FAIL: CD Level 7 crashed with {e}")

    # Test Max Config Levels
    print("\nTesting Max Config Levels (Level 10)...")
    print("CD Level 10:")
    try:
        generate_unit_shape(10, 0, 0, 10, 0, 0)
        print("Success.")
    except Exception as e:
        print(f"FAIL: {e}")

    print("DMG Level 10:")
    try:
        generate_unit_shape(10, 0, 10, 0, 0, 0)
        print("Success.")
    except Exception as e:
        print(f"FAIL: {e}")

    print("Range Level 10:")
    try:
        generate_unit_shape(10, 0, 0, 0, 0, 10)
        print("Success.")
    except Exception as e:
        print(f"FAIL: {e}")

    print("\nTesting Combined Max Levels:")
    try:
        generate_unit_shape(10, 10, 10, 10, 10, 10)
        print("Success.")
    except Exception as e:
        print(f"FAIL: {e}")

if __name__ == "__main__":
    test_shapes()
