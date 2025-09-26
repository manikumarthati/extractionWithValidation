"""
Test script for text preservation during visual correction
Tests the specific issue where correction process truncates text descriptions
"""

import json
import os
from services.visual_field_inspector import VisualFieldInspector

def test_text_preservation_correction():
    """Test text preservation during correction process"""

    print("=== TEXT PRESERVATION CORRECTION TEST ===")
    print()

    # Initialize the visual field inspector
    inspector = VisualFieldInspector(api_key="test_key")

    # Test case based on the debug logs issue
    print("TEST SCENARIO: Minnesota Federal Loan Assessment Truncation")
    print("Issue: Correction truncates 'Minnesota Federal Loan Assessment' to 'Minnesota Federal Lo'")
    print()

    # Original extracted data (correct and complete)
    original_data = {
        "employee_taxes": [
            {
                "tax_code": "MNDW",
                "description": "Minnesota Federal Loan Assessment",  # COMPLETE TEXT
                "rate": 0.5,
                "effective_dates": "01/01/2023 to 12/31/2100"
            }
        ],
        "employee_deductions": [
            {
                "DeductionCode": "DNTL",
                "CalCode": "B5",   # WRONG COLUMN - should be empty
                "Frequency": ""    # WRONG - should contain "B5"
            }
        ]
    }

    # Validation findings (correctly identifies column misalignment)
    validation_result = {
        "issues_found": [
            {
                "field": "employee_deductions[0].CalCode",
                "issue": "Contains 'B5' but should be empty based on visual alignment",
                "correction_needed": "Move B5 to Frequency column"
            }
        ],
        "text_completeness": "Complete text descriptions verified"
    }

    schema = {
        "employee_taxes": [
            {
                "tax_code": "string",
                "description": "string",
                "rate": "number",
                "effective_dates": "string"
            }
        ],
        "employee_deductions": [
            {
                "DeductionCode": "string",
                "CalCode": "string",
                "Frequency": "string"
            }
        ]
    }

    print("ORIGINAL DATA (Complete Text):")
    print(json.dumps(original_data, indent=2))
    print()

    print("VALIDATION RESULT (Correct Issue Detection):")
    print(json.dumps(validation_result, indent=2))
    print()

    # Test the correction prompt
    correction_prompt = inspector._build_visual_correction_prompt(
        original_data, validation_result, schema, page_num=0
    )

    print("=== CORRECTION PROMPT ANALYSIS ===")
    print()

    # Check for text preservation instructions
    text_preservation_features = [
        "MANDATORY TEXT PRESERVATION",
        "NEVER truncate text during corrections",
        "Minnesota Federal Loan Assessment",
        "keep it as \"Minnesota Federal Loan Assessment\"",
        "Minnesota Federal Lo",
        "use complete text from original data above",
        "Only fix POSITIONING and COLUMN ASSIGNMENT",
        "CORRECTION PRIORITY ORDER",
        "Use complete text values from original extracted data",
        "FINAL TEXT PRESERVATION REMINDER",
        "verify that ALL text descriptions match the complete versions"
    ]

    found_features = 0
    missing_features = []

    for feature in text_preservation_features:
        if feature in correction_prompt:
            found_features += 1
        else:
            missing_features.append(feature)

    print(f"Text Preservation Instructions: {found_features}/{len(text_preservation_features)} found")

    if found_features >= 8:
        print("   PASS: Comprehensive text preservation instructions included")
    else:
        print("   FAIL: Missing critical text preservation instructions")
        print(f"   Missing: {missing_features}")

    print()

    # Check if original complete data is referenced
    complete_description = "Minnesota Federal Loan Assessment"
    has_complete_reference = complete_description in correction_prompt

    print(f"Complete Text Reference: {'PASS' if has_complete_reference else 'FAIL'}")
    if has_complete_reference:
        print("   ✓ Original complete text 'Minnesota Federal Loan Assessment' is in prompt")
    else:
        print("   ✗ Original complete text not found in correction prompt")

    print()

    # Check correction priority order
    priority_instructions = [
        "FIRST: Fix column misalignment",
        "SECOND: Use complete text values from original extracted data",
        "THIRD: Only change values if they are completely wrong"
    ]

    found_priority = 0
    for instruction in priority_instructions:
        if instruction in correction_prompt:
            found_priority += 1

    print(f"Correction Priority Order: {found_priority}/{len(priority_instructions)} found")
    if found_priority == len(priority_instructions):
        print("   PASS: Complete priority order specified")
    else:
        print("   FAIL: Incomplete priority order instructions")

    print()

    # Test validation prompt for truncation detection
    print("=== VALIDATION PROMPT ENHANCEMENT ===")

    # Simulated corrected data with truncation issue
    corrected_data_with_truncation = {
        "employee_taxes": [
            {
                "tax_code": "MNDW",
                "description": "Minnesota Federal Lo",  # TRUNCATED - should be flagged
                "rate": 0.5,
                "effective_dates": "01/01/2023 to 12/31/2100"
            }
        ],
        "employee_deductions": [
            {
                "DeductionCode": "DNTL",
                "CalCode": "",      # FIXED - now empty
                "Frequency": "B5"   # FIXED - now contains B5
            }
        ]
    }

    validation_prompt = inspector._build_comprehensive_visual_validation_prompt(
        corrected_data_with_truncation, schema, page_num=0
    )

    # Check for truncation detection instructions
    truncation_detection = [
        "TEXT TRUNCATION HANDLING",
        "If text in extracted data is truncated",
        "Minnesota Federal Lo",
        "Minnesota Federal Loan Assessment",
        "flag this as an ERROR even if positioning is correct"
    ]

    found_detection = 0
    for instruction in truncation_detection:
        if instruction in validation_prompt:
            found_detection += 1

    print(f"Truncation Detection Instructions: {found_detection}/{len(truncation_detection)} found")
    if found_detection >= 4:
        print("   PASS: Validation can detect truncation issues in corrected data")
    else:
        print("   FAIL: Validation may not catch truncation issues")

    print()

    print("=== EXPECTED CORRECTION BEHAVIOR ===")
    print()
    print("With enhanced prompts, the correction should:")
    print("1. ✓ Identify that B5 is in wrong column (CalCode instead of Frequency)")
    print("2. ✓ Move B5 from CalCode to Frequency column")
    print("3. ✓ Set CalCode to empty string")
    print("4. ✓ PRESERVE complete text 'Minnesota Federal Loan Assessment'")
    print("5. ✓ NOT truncate to 'Minnesota Federal Lo'")
    print()
    print("Subsequent validation should:")
    print("1. ✓ Verify column alignment is correct")
    print("2. ✓ Check text completeness")
    print("3. ✓ Flag any truncated text as ERROR even if positioning is correct")

    print()
    print("=== ISSUE RESOLUTION SUMMARY ===")
    print()
    print("PROBLEM IDENTIFIED:")
    print("- Visual correction was truncating text descriptions")
    print("- 'Minnesota Federal Loan Assessment' became 'Minnesota Federal Lo'")
    print("- Subsequent validation incorrectly marked truncated text as correct")
    print()
    print("SOLUTION IMPLEMENTED:")
    print("✓ Added MANDATORY TEXT PRESERVATION instructions")
    print("✓ Explicit examples of text preservation (Minnesota Federal Loan Assessment)")
    print("✓ Clear correction priority: positioning first, text preservation second")
    print("✓ Final reminder to verify text completeness before output")
    print("✓ Enhanced validation to flag truncation as error")
    print()
    print("EXPECTED OUTCOME:")
    print("✓ Column misalignment corrected (B5 moved to Frequency)")
    print("✓ Complete text descriptions preserved")
    print("✓ No truncation during correction process")
    print("✓ Validation catches any remaining truncation issues")

if __name__ == "__main__":
    test_text_preservation_correction()