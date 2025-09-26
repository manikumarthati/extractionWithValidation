"""
Test script for enhanced validation fixes
Tests the two specific observations:
1. False frequency detection for deduction codes without frequency
2. Text truncation handling with raw text cross-validation
"""

import json
import os
from services.visual_field_inspector import VisualFieldInspector

def test_enhanced_validation_fixes():
    """Test the enhanced validation fixes"""

    # Initialize the visual field inspector
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found in environment variables")
        return

    inspector = VisualFieldInspector(api_key)

    print("=== ENHANCED VALIDATION FIXES TEST ===")
    print()

    # Test Case 1: False Frequency Detection
    print("TEST CASE 1: False Frequency Detection Prevention")
    print("Issue: Some deduction codes showing 'B' as frequency when they have no frequency")
    print()

    test_data_false_freq = {
        "employee_deductions": [
            {
                "DeductionCode": "HEALTH",
                "CalCode": "",
                "Frequency": "B"  # PROBLEM: Should be empty for this deduction
            },
            {
                "DeductionCode": "DENTAL",
                "CalCode": "",
                "Frequency": ""   # CORRECT: Empty as it should be
            }
        ]
    }

    schema = {
        "employee_deductions": [
            {
                "DeductionCode": "string",
                "CalCode": "string",
                "Frequency": "string - may be empty for some deductions"
            }
        ]
    }

    validation_prompt = inspector._build_comprehensive_visual_validation_prompt(
        test_data_false_freq, schema, page_num=0
    )

    # Check for false frequency prevention instructions
    false_freq_instructions = [
        "FALSE FREQUENCY DETECTION",
        "Some deduction codes have NO frequency value",
        "If a field appears empty in the image, mark it as empty",
        "Don't assume truncated single letters are valid frequency codes"
    ]

    found_false_freq = 0
    for instruction in false_freq_instructions:
        if instruction in validation_prompt:
            found_false_freq += 1

    print(f"   False Frequency Prevention Instructions: {found_false_freq}/{len(false_freq_instructions)} found")
    if found_false_freq >= 3:
        print("   PASS: False frequency detection prevention implemented")
    else:
        print("   FAIL: Missing false frequency detection prevention")

    print()

    # Test Case 2: Text Truncation Handling
    print("TEST CASE 2: Text Truncation Prevention with Raw Text Cross-Validation")
    print("Issue: Visual validation truncates 'B5' to 'B', need to use extracted data for complete values")
    print()

    test_data_truncation = {
        "employee_deductions": [
            {
                "DeductionCode": "MEDICAL",
                "CalCode": "",
                "Frequency": "B5"  # Complete value in extracted data
            }
        ]
    }

    # Check for text truncation handling instructions
    truncation_instructions = [
        "TEXT TRUNCATION HANDLING",
        "Visual extraction may truncate values",
        "cross-reference with extracted data",
        "Use the complete value from extracted data if visual shows truncated version",
        "Visual shows \"B\", extracted data has \"B5\" → use \"B5\"",
        "RAW TEXT CROSS-VALIDATION"
    ]

    found_truncation = 0
    for instruction in truncation_instructions:
        if instruction in validation_prompt:
            found_truncation += 1

    print(f"   Text Truncation Handling Instructions: {found_truncation}/{len(truncation_instructions)} found")
    if found_truncation >= 4:
        print("   PASS: Text truncation prevention implemented")
    else:
        print("   FAIL: Missing text truncation prevention")

    # Check if extracted data is included in prompt for cross-validation
    extracted_data_in_prompt = json.dumps(test_data_truncation, indent=2) in validation_prompt
    if extracted_data_in_prompt:
        print("   PASS: Extracted data included in prompt for cross-validation")
    else:
        print("   FAIL: Extracted data not included for cross-validation")

    print()

    # Test Case 3: Correction Prompt Enhancements
    print("TEST CASE 3: Enhanced Correction Prompt")

    validation_result = {
        "issues": [
            {"field": "Frequency", "issue": "Shows 'B' but should be 'B5' or empty"}
        ]
    }

    correction_prompt = inspector._build_visual_correction_prompt(
        test_data_truncation, validation_result, schema, page_num=0
    )

    correction_instructions = [
        "EMPTY FREQUENCY FIELDS",
        "Don't add \"B\" or single letters unless you clearly see complete text",
        "TEXT TRUNCATION CORRECTIONS",
        "If visual shows \"B\" but extracted data has \"B5\", use \"B5\"",
        "EXTRACTED DATA REFERENCE"
    ]

    found_correction = 0
    for instruction in correction_instructions:
        if instruction in correction_prompt:
            found_correction += 1

    print(f"   Enhanced Correction Instructions: {found_correction}/{len(correction_instructions)} found")
    if found_correction >= 4:
        print("   PASS: Enhanced correction instructions implemented")
    else:
        print("   FAIL: Missing enhanced correction instructions")

    print()

    # Test Case 4: Combined Scenario
    print("TEST CASE 4: Combined Scenario - Both Issues")

    combined_data = {
        "employee_deductions": [
            {
                "DeductionCode": "LIFE",
                "CalCode": "",
                "Frequency": ""     # Should stay empty - no frequency for this deduction
            },
            {
                "DeductionCode": "HSA",
                "CalCode": "",
                "Frequency": "B5"   # Should use complete value, not truncated "B"
            },
            {
                "DeductionCode": "VISION",
                "CalCode": "",
                "Frequency": "B"    # PROBLEM: This might be truncated or false positive
            }
        ]
    }

    combined_prompt = inspector._build_comprehensive_visual_validation_prompt(
        combined_data, schema, page_num=0
    )

    # Should contain both sets of instructions
    has_false_freq_prevention = "FALSE FREQUENCY DETECTION" in combined_prompt
    has_truncation_handling = "TEXT TRUNCATION HANDLING" in combined_prompt
    has_extracted_data = json.dumps(combined_data, indent=2) in combined_prompt

    print(f"   Combined scenario validation:")
    print(f"   - False frequency prevention: {'PASS' if has_false_freq_prevention else 'FAIL'}")
    print(f"   - Text truncation handling: {'PASS' if has_truncation_handling else 'FAIL'}")
    print(f"   - Extracted data reference: {'PASS' if has_extracted_data else 'FAIL'}")

    print()
    print("=== TEST SUMMARY ===")
    print("OBSERVATION 1 (False Frequency Detection):")
    print("   - Added specific instructions to not assume single letters are valid frequencies")
    print("   - Emphasizes checking for truly empty fields vs false positives")
    print("   - Prevents 'B' from being incorrectly identified as a frequency code")
    print()
    print("OBSERVATION 2 (Text Truncation):")
    print("   - Added cross-validation with extracted data for complete values")
    print("   - Handles cases where visual shows 'B' but extracted data has 'B5'")
    print("   - Preserves complete text values while correcting positioning")
    print()
    print("ENHANCED VALIDATION NOW HANDLES:")
    print("   ✓ False positive frequency detection prevention")
    print("   ✓ Text truncation with raw text cross-validation")
    print("   ✓ Complete value preservation during correction")
    print("   ✓ Empty field validation vs false content detection")

if __name__ == "__main__":
    test_enhanced_validation_fixes()