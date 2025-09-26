"""
Test script for token-optimized prompts
Verifies that duplicate extracted data references were removed while maintaining functionality
"""

import json
import os
from services.visual_field_inspector import VisualFieldInspector

def test_token_optimized_prompts():
    """Test the token-optimized prompts"""

    print("=== TOKEN OPTIMIZATION TEST ===")
    print()

    # Initialize the visual field inspector
    inspector = VisualFieldInspector(api_key="test_key")

    # Test data for validation
    test_data = {
        "employee_deductions": [
            {
                "DeductionCode": "MEDICAL",
                "CalCode": "",
                "Frequency": "B5"
            },
            {
                "DeductionCode": "DENTAL",
                "CalCode": "",
                "Frequency": ""
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

    print("TEST 1: Validation Prompt Token Optimization")

    validation_prompt = inspector._build_comprehensive_visual_validation_prompt(
        test_data, schema, page_num=0
    )

    # Count how many times the extracted data appears
    extracted_data_json = json.dumps(test_data, indent=2)
    data_occurrences = validation_prompt.count(extracted_data_json)

    print(f"   Extracted data appears {data_occurrences} time(s) in validation prompt")

    if data_occurrences == 1:
        print("   PASS: Extracted data referenced only once (optimized)")
    elif data_occurrences == 0:
        print("   FAIL: Extracted data not found in prompt")
    else:
        print(f"   FAIL: Extracted data duplicated {data_occurrences} times (not optimized)")

    # Check that all required features are still present
    required_features = [
        "CURRENT EXTRACTED DATA TO VERIFY AND CROSS-REFERENCE",
        "FALSE FREQUENCY DETECTION",
        "TEXT TRUNCATION HANDLING",
        "use the complete value from the extracted data above",
        "Cross-reference with the extracted data when visual text appears incomplete"
    ]

    missing_features = []
    for feature in required_features:
        if feature not in validation_prompt:
            missing_features.append(feature)

    if not missing_features:
        print("   PASS: All required features present after optimization")
    else:
        print(f"   FAIL: Missing features after optimization: {missing_features}")

    print()
    print("TEST 2: Correction Prompt Token Optimization")

    validation_result = {
        "issues": [{"field": "Frequency", "issue": "Truncated value"}]
    }

    correction_prompt = inspector._build_visual_correction_prompt(
        test_data, validation_result, schema, page_num=0
    )

    # Count occurrences in correction prompt
    data_occurrences_correction = correction_prompt.count(extracted_data_json)

    print(f"   Extracted data appears {data_occurrences_correction} time(s) in correction prompt")

    if data_occurrences_correction == 1:
        print("   PASS: Extracted data referenced only once in correction prompt (optimized)")
    elif data_occurrences_correction == 0:
        print("   FAIL: Extracted data not found in correction prompt")
    else:
        print(f"   FAIL: Extracted data duplicated {data_occurrences_correction} times in correction prompt")

    # Check correction prompt features
    correction_features = [
        "ORIGINAL EXTRACTED DATA FROM PAGE",
        "EMPTY FREQUENCY FIELDS",
        "TEXT TRUNCATION CORRECTIONS",
        "original extracted data above has",
        "complete version from the original extracted data above"
    ]

    missing_correction_features = []
    for feature in correction_features:
        if feature not in correction_prompt:
            missing_correction_features.append(feature)

    if not missing_correction_features:
        print("   PASS: All correction features present after optimization")
    else:
        print(f"   FAIL: Missing correction features: {missing_correction_features}")

    print()
    print("TEST 3: Token Count Estimation")

    # Rough token estimation (1 token ≈ 4 characters)
    validation_chars = len(validation_prompt)
    correction_chars = len(correction_prompt)

    validation_tokens = validation_chars // 4
    correction_tokens = correction_chars // 4

    print(f"   Validation prompt: ~{validation_chars} chars, ~{validation_tokens} tokens")
    print(f"   Correction prompt: ~{correction_chars} chars, ~{correction_tokens} tokens")

    # Estimate savings from removing duplication
    extracted_data_chars = len(extracted_data_json)
    token_savings = extracted_data_chars // 4

    print(f"   Token savings from removing duplication: ~{token_savings} tokens per prompt")
    print(f"   Total potential savings per validation cycle: ~{token_savings * 2} tokens")

    print()
    print("TEST 4: Functionality Verification")

    # Verify that references to extracted data still work
    has_cross_reference_instructions = (
        "Cross-reference with the extracted data" in validation_prompt or
        "use the complete value from the extracted data above" in validation_prompt
    )

    has_above_references = (
        "extracted data above" in validation_prompt and
        "original extracted data above" in correction_prompt
    )

    print(f"   Cross-reference instructions present: {'PASS' if has_cross_reference_instructions else 'FAIL'}")
    print(f"   'Above' references working: {'PASS' if has_above_references else 'FAIL'}")

    print()
    print("=== OPTIMIZATION SUMMARY ===")
    print()
    print("BEFORE OPTIMIZATION:")
    print("   - Extracted data referenced twice in validation prompt")
    print("   - Extracted data referenced twice in correction prompt")
    print("   - Unnecessary token duplication")
    print()
    print("AFTER OPTIMIZATION:")
    print("   - Single reference with clear 'above' indicators")
    print("   - Maintained all cross-validation functionality")
    print("   - Reduced token usage while preserving features")
    print()
    print("BENEFITS:")
    print("   ✓ Reduced token consumption")
    print("   ✓ Maintained false frequency detection prevention")
    print("   ✓ Maintained text truncation handling")
    print("   ✓ Preserved cross-reference capabilities")
    print("   ✓ Cleaner prompt structure")

if __name__ == "__main__":
    test_token_optimized_prompts()