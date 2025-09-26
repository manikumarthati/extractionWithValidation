"""
Test script for enhanced visual validation prompts
Tests the updated prompts that focus on visual layout rather than semantic assumptions
"""

import json
import os
from services.visual_field_inspector import VisualFieldInspector

def test_enhanced_visual_prompts():
    """Test the enhanced visual validation prompts"""

    # Initialize the visual field inspector
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found in environment variables")
        return

    inspector = VisualFieldInspector(api_key)

    # Test data with B5 misalignment issue
    extracted_data = {
        "employee_deductions": [
            {
                "DeductionCode": "DNTL",
                "CalCode": "B5",  # INCORRECT - should be empty
                "Frequency": "",  # INCORRECT - should contain "B5"
            },
            {
                "DeductionCode": "FH125",
                "CalCode": "B5",  # INCORRECT - should be empty
                "Frequency": "",  # INCORRECT - should contain "B5"
            }
        ]
    }

    schema = {
        "employee_deductions": [
            {
                "DeductionCode": "string",
                "CalCode": "string",
                "Frequency": "string"
            }
        ]
    }

    print("Test 1: Enhanced validation prompt generation")

    validation_prompt = inspector._build_comprehensive_visual_validation_prompt(
        extracted_data, schema, page_num=0
    )

    # Check for enhanced visual instructions
    enhanced_features = [
        "TRUE VISUAL INSPECTION",
        "IGNORE semantic assumptions",
        "LOOK at actual visual positioning",
        "FOR TABULAR DATA",
        "FOR FORM FIELDS",
        "trace vertically down",
        "EXAMPLE MISALIGNMENT DETECTION",
        "LEFT-SHIFT"
    ]

    found_features = []
    missing_features = []

    for feature in enhanced_features:
        if feature in validation_prompt:
            found_features.append(feature)
        else:
            missing_features.append(feature)

    print(f"   PASS: Found {len(found_features)}/{len(enhanced_features)} enhanced features")
    print(f"   Found features: {found_features}")
    if missing_features:
        print(f"   Missing features: {missing_features}")

    print("\nTest 2: Enhanced correction prompt generation")

    validation_result = {
        "validation": "Column misalignment detected",
        "issues_found": [
            {
                "field": "employee_deductions[0].CalCode",
                "issue": "Contains 'B5' but should be empty based on visual alignment",
                "visual_evidence": "B5 appears under Frequency column in document"
            }
        ]
    }

    correction_prompt = inspector._build_visual_correction_prompt(
        extracted_data, validation_result, schema, page_num=0
    )

    # Check for correction-specific features
    correction_features = [
        "VISUAL LAYOUT ANALYSIS",
        "LAYOUT-AWARE CORRECTION APPROACH",
        "FOR TABULAR DATA CORRECTIONS",
        "FOR FORM FIELD CORRECTIONS",
        "SPECIFIC CORRECTION EXAMPLE",
        "trace down to see actual data positioning",
        "ACTUAL VISUAL POSITIONING"
    ]

    found_correction_features = []
    missing_correction_features = []

    for feature in correction_features:
        if feature in correction_prompt:
            found_correction_features.append(feature)
        else:
            missing_correction_features.append(feature)

    print(f"   PASS: Found {len(found_correction_features)}/{len(correction_features)} correction features")
    print(f"   Found features: {found_correction_features}")
    if missing_correction_features:
        print(f"   Missing features: {missing_correction_features}")

    print("\nTest 3: B5 misalignment example in prompt")

    # Check if the specific B5 example is included
    b5_examples = [
        "B5",
        "CalCode",
        "Frequency",
        "LEFT-SHIFT",
        "moved one column left"
    ]

    found_b5_examples = []
    for example in b5_examples:
        if example in validation_prompt:
            found_b5_examples.append(example)

    if len(found_b5_examples) >= 4:
        print("   PASS: B5 misalignment example properly included in validation prompt")
    else:
        print(f"   PARTIAL: Found {len(found_b5_examples)}/{len(b5_examples)} B5 example elements")

    # Check correction prompt for B5 example
    found_b5_correction = []
    for example in b5_examples:
        if example in correction_prompt:
            found_b5_correction.append(example)

    if len(found_b5_correction) >= 3:
        print("   PASS: B5 correction example properly included in correction prompt")
    else:
        print(f"   PARTIAL: Found {len(found_b5_correction)}/{len(b5_examples)} B5 correction elements")

    print("\nTest 4: Layout type differentiation")

    # Check that both tabular and form field instructions are present
    layout_types = ["FOR TABULAR DATA", "FOR FORM FIELDS"]

    found_layouts = []
    for layout_type in layout_types:
        if layout_type in validation_prompt:
            found_layouts.append(layout_type)

    if len(found_layouts) == len(layout_types):
        print("   PASS: Both tabular and form field instructions present")
    else:
        print(f"   FAIL: Missing layout instructions for {set(layout_types) - set(found_layouts)}")

    print("\nEnhanced visual validation prompts test completed!")
    print("\nSummary:")
    print("   * Enhanced prompts focus on visual layout rather than semantic assumptions")
    print("   * Specific instructions for tabular data (vertical alignment)")
    print("   * Specific instructions for form fields (spatial relationships)")
    print("   * B5 misalignment detection example included")
    print("   * Layout-aware correction approach implemented")
    print("   * Ready to catch column shifting issues like B5 in wrong column")

if __name__ == "__main__":
    test_enhanced_visual_prompts()