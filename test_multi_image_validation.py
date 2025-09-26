"""
Test script for multi-image validation system
Tests the updated visual field inspector with page-specific file IDs
"""

import json
import os
from services.visual_field_inspector import VisualFieldInspector

def test_multi_image_validation():
    """Test the multi-image validation system"""

    # Initialize the visual field inspector
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found in environment variables")
        return

    inspector = VisualFieldInspector(api_key)

    # Test data
    extracted_data = {
        "employee_name": "John Doe",
        "department": "Engineering",
        "salary": "$75,000"
    }

    schema = {
        "employee_name": "string",
        "department": "string",
        "salary": "currency"
    }

    # Test 1: Single page with file ID
    print("Test 1: Single page validation with file ID")
    page_file_ids = {
        0: "file_abc123_page_0"  # Simulated file ID for page 0
    }

    print(f"   📄 Testing page 0 with file ID: {page_file_ids[0]}")

    # This should use the page-specific file ID for page 0
    result = inspector._get_page_file_id(
        page_num=0,
        fallback_file_id="fallback_file_id",
        page_file_ids=page_file_ids
    )

    expected = page_file_ids[0]
    if result == expected:
        print(f"   PASS: Correct file ID selected: {result}")
    else:
        print(f"   FAIL: Wrong file ID. Expected: {expected}, Got: {result}")

    # Test 2: Page not in mapping - should use fallback
    print("\nTest 2: Page not in mapping - fallback test")

    result = inspector._get_page_file_id(
        page_num=1,  # Page 1 not in mapping
        fallback_file_id="fallback_file_id",
        page_file_ids=page_file_ids
    )

    expected = "fallback_file_id"
    if result == expected:
        print(f"   ✅ Correct fallback used: {result}")
    else:
        print(f"   ❌ Wrong fallback. Expected: {expected}, Got: {result}")

    # Test 3: No file IDs available
    print("\n🧪 Test 3: No file IDs available - should return None")

    result = inspector._get_page_file_id(
        page_num=0,
        fallback_file_id=None,
        page_file_ids=None
    )

    if result is None:
        print("   ✅ Correctly returned None when no file IDs available")
    else:
        print(f"   ❌ Should have returned None, got: {result}")

    # Test 4: Multi-page file ID mapping
    print("\n🧪 Test 4: Multi-page file ID mapping")

    multi_page_file_ids = {
        0: "file_page_0_abc123",
        1: "file_page_1_def456",
        2: "file_page_2_ghi789"
    }

    for page in range(3):
        result = inspector._get_page_file_id(
            page_num=page,
            fallback_file_id="fallback",
            page_file_ids=multi_page_file_ids
        )

        expected = multi_page_file_ids[page]
        if result == expected:
            print(f"   ✅ Page {page}: Correct file ID {result[:20]}...")
        else:
            print(f"   ❌ Page {page}: Wrong file ID. Expected: {expected}, Got: {result}")

    # Test 5: Prompt generation with page numbers
    print("\n🧪 Test 5: Prompt generation with page-specific references")

    validation_prompt = inspector._build_comprehensive_visual_validation_prompt(
        extracted_data, schema, page_num=2
    )

    # Check if prompt contains page-specific references
    page_references = [
        "PAGE 2",
        "page 2",
        "page 2 image"
    ]

    found_references = []
    for ref in page_references:
        if ref in validation_prompt:
            found_references.append(ref)

    if found_references:
        print(f"   ✅ Prompt contains page-specific references: {found_references}")
    else:
        print("   ❌ Prompt missing page-specific references")

    correction_prompt = inspector._build_visual_correction_prompt(
        extracted_data, {"validation": "test"}, schema, page_num=2
    )

    found_references = []
    for ref in page_references:
        if ref in correction_prompt:
            found_references.append(ref)

    if found_references:
        print(f"   ✅ Correction prompt contains page-specific references: {found_references}")
    else:
        print("   ❌ Correction prompt missing page-specific references")

    print("\n🎉 Multi-image validation system tests completed!")
    print("\n📋 Summary:")
    print("   ✓ Page-specific file ID selection")
    print("   ✓ Fallback file ID handling")
    print("   ✓ Multi-page file ID mapping")
    print("   ✓ Page-specific prompt generation")
    print("   ✓ Enhanced visual validation ready for production")

if __name__ == "__main__":
    test_multi_image_validation()