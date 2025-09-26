#!/usr/bin/env python3
"""
Test script to verify the 'bad filter size' fix
"""

from PIL import Image, ImageFilter, ImageEnhance
import numpy as np

def test_median_filter():
    """Test MedianFilter with different sizes"""
    print("Testing MedianFilter sizes...")
    print("=" * 40)

    # Create a test image
    test_image = Image.new('RGB', (100, 100), color='white')

    test_cases = [
        (1, "Should work (odd size)"),
        (2, "Should fail (even size)"),
        (3, "Should work (odd size)"),
        (5, "Should work (odd size)"),
    ]

    for size, description in test_cases:
        try:
            filtered_image = test_image.filter(ImageFilter.MedianFilter(size=size))
            print(f"MedianFilter(size={size}): [OK] - {description}")
        except ValueError as e:
            print(f"MedianFilter(size={size}): [ERROR] - {e}")

def test_image_enhancement():
    """Test the image enhancement pipeline"""
    print("\nTesting image enhancement pipeline...")
    print("=" * 40)

    # Test with different image sizes
    test_sizes = [
        (1, 1, "Tiny image"),
        (2, 2, "Very small image"),
        (10, 10, "Small image"),
        (100, 100, "Normal image"),
    ]

    for width, height, description in test_sizes:
        try:
            # Create test image
            image = Image.new('RGB', (width, height), color='gray')

            # Test enhancement steps
            print(f"\nTesting {description} ({width}x{height}):")

            # Check minimum dimensions
            if width < 10 or height < 10:
                print(f"  Size check: Image too small, skipping enhancement")
                continue

            # Sharpness enhancement
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.3)
            print(f"  Sharpness: [OK]")

            # Contrast enhancement
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.15)
            print(f"  Contrast: [OK]")

            # MedianFilter with size check
            if width >= 3 and height >= 3:
                image = image.filter(ImageFilter.MedianFilter(size=3))
                print(f"  MedianFilter: [OK]")
            else:
                print(f"  MedianFilter: [SKIPPED] - Image too small")

        except Exception as e:
            print(f"  Enhancement failed: [ERROR] - {e}")

def main():
    """Run all tests"""
    print("Filter Size Error Fix Test")
    print("=" * 50)

    test_median_filter()
    test_image_enhancement()

    print("\n" + "=" * 50)
    print("Test Summary:")
    print("- Fixed MedianFilter to use size=3 (odd number)")
    print("- Added dimension checks before applying filters")
    print("- Added error handling for robustness")
    print("\nThe 'bad filter size' error should be resolved!")

if __name__ == "__main__":
    main()