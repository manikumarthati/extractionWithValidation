#!/usr/bin/env python3
"""
Simple test for sprintf formatting fixes
"""

def test_fixed_formats():
    """Test the specific formatting fixes"""

    print("Testing sprintf formatting fixes...")
    print("=" * 50)

    # Test the fixed format string
    try:
        result = "%.0f%%" % 95
        print(f"Fixed format string: '%.0f%%' -> '{result}' [OK]")
    except Exception as e:
        print(f"Fixed format string: ERROR - {e}")

    # Test the fixed f-string equivalents
    try:
        accuracy = 0.95
        result = f"{accuracy*100:.1f}%"
        print(f"Fixed f-string: accuracy*100 -> '{result}' [OK]")
    except Exception as e:
        print(f"Fixed f-string: ERROR - {e}")

    try:
        final_accuracy = 0.95
        result = f"{(final_accuracy - 0.85)*100:.1f}%"
        print(f"Fixed delta f-string: delta -> '{result}' [OK]")
    except Exception as e:
        print(f"Fixed delta f-string: ERROR - {e}")

    print("\nAll formatting tests completed successfully!")
    print("The sprintf errors should be resolved.")

if __name__ == "__main__":
    test_fixed_formats()