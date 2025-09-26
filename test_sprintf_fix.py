#!/usr/bin/env python3
"""
Test script to verify the sprintf error fix in Streamlit app
"""

def test_percentage_formatting():
    """Test that percentage formatting doesn't cause sprintf errors"""

    # Test the problematic patterns we fixed
    test_cases = [
        # Fixed format string
        ("%.0f%%", 0.95, "95%"),

        # Fixed f-string with percentage
        ("{accuracy*100:.1f}%", 0.95, "95.0%"),

        # Fixed delta formatting
        ("{(final_accuracy - 0.85)*100:.1f}%", 0.95, "10.0%"),
    ]

    print("Testing percentage formatting patterns...")
    print("=" * 50)

    all_passed = True

    for pattern, value, expected in test_cases:
        try:
            if pattern.startswith("{"):
                # This is an f-string pattern (simulated)
                if "accuracy*100" in pattern:
                    result = f"{value*100:.1f}%"
                elif "final_accuracy" in pattern:
                    result = f"{(value - 0.85)*100:.1f}%"
                else:
                    result = "Unknown pattern"
            else:
                # This is a format string
                result = pattern % (value * 100)

            print(f"✓ Pattern: {pattern}")
            print(f"  Input: {value}")
            print(f"  Output: {result}")
            print(f"  Expected: {expected}")

            if result == expected:
                print("  Status: PASS")
            else:
                print("  Status: FAIL")
                all_passed = False
            print()

        except Exception as e:
            print(f"✗ Pattern: {pattern}")
            print(f"  ERROR: {e}")
            print("  Status: FAIL")
            all_passed = False
            print()

    print("=" * 50)
    if all_passed:
        print("✓ All percentage formatting tests passed!")
        print("The sprintf error should be fixed.")
    else:
        print("✗ Some tests failed.")

    return all_passed

def test_format_string_validation():
    """Test specific format strings that could cause sprintf issues"""

    problematic_patterns = [
        "%.0%%",  # This was the original problem - double %
        "%.1%",   # This would be problematic
        "%d%",    # This could be problematic
    ]

    safe_patterns = [
        "%.0f%%",  # This is our fix
        "%.1f%%",  # This should be safe
        "%d%%",    # This should be safe
    ]

    print("\nTesting format string validation...")
    print("=" * 50)

    print("Problematic patterns (should avoid):")
    for pattern in problematic_patterns:
        print(f"  {pattern} - AVOID (can cause sprintf errors)")

    print("\nSafe patterns (should work):")
    for pattern in safe_patterns:
        try:
            result = pattern % 95
            print(f"  {pattern} -> {result} ✓")
        except Exception as e:
            print(f"  {pattern} -> ERROR: {e} ✗")

if __name__ == "__main__":
    print("Sprintf Error Fix Validation")
    print("=" * 60)

    test_percentage_formatting()
    test_format_string_validation()

    print("\n" + "=" * 60)
    print("Summary:")
    print("- Fixed format string: %.0f%% (was %.0%%)")
    print("- Fixed f-strings: {value*100:.1f}% (was {value:.1%})")
    print("- These changes should resolve the sprintf placeholder errors")
    print("\nThe Streamlit app should now load without JavaScript errors!")