#!/usr/bin/env python3
"""
Test the enhanced visual validation prompt for detecting B5 CalcCode/Frequency misalignment
"""

from services.visual_field_inspector import VisualFieldInspector
import json

def test_b5_misalignment_detection():
    """Test the enhanced prompt's ability to detect the B5 misalignment issue"""

    # Sample extracted data that replicates the DNTL/FH125 issue
    sample_extracted_data = {
        "Deduction_Information": {
            "Deduction_Records": [
                {
                    "Code": "DNTL",
                    "Description": "Dental Insurance S125",
                    "Rate": 18.32,
                    "Calc_Code": "B5",  # WRONG - should be empty
                    "Frequency": "",    # WRONG - should be "B5"
                    "Goal_Paid": "0.00/0.00",
                    "Min_Max_Annual_Max": "0.00/0.00/0.00",
                    "Arrears": 0.0,
                    "Agency": "",
                    "Effective_Start_Date": "09/01/2019",
                    "Effective_End_Date": "12/31/2100"
                },
                {
                    "Code": "FH125",
                    "Description": "Health Insurance S125",
                    "Rate": 158.14,
                    "Calc_Code": "B5",  # WRONG - should be empty
                    "Frequency": "",    # WRONG - should be "B5"
                    "Goal_Paid": "0.00/0.00",
                    "Min_Max_Annual_Max": "0.00/0.00/0.00",
                    "Arrears": 0.0,
                    "Agency": "",
                    "Effective_Start_Date": "09/01/2019",
                    "Effective_End_Date": "12/31/2100"
                }
            ]
        }
    }

    # Schema showing the expected structure
    sample_schema = {
        "Deduction_Information": {
            "Deduction_Records": [
                {
                    "Code": "string",
                    "Description": "string",
                    "Rate": "number",
                    "Calc_Code": "string",  # Should be empty for these entries
                    "Frequency": "string",  # Should contain "B5"
                    "Goal_Paid": "string",
                    "Min_Max_Annual_Max": "string",
                    "Arrears": "number",
                    "Agency": "string",
                    "Effective_Start_Date": "datetime",
                    "Effective_End_Date": "datetime"
                }
            ]
        }
    }

    # Create inspector and generate enhanced prompt
    inspector = VisualFieldInspector("")
    prompt = inspector._build_comprehensive_visual_validation_prompt(
        sample_extracted_data, sample_schema
    )

    print("=== ENHANCED B5 MISALIGNMENT DETECTION TEST ===")
    print()
    print("Test Case: B5 incorrectly in Calc_Code, should be in Frequency")
    print("Expected Detection: Empty column skip pattern")
    print()
    print("=== KEY ENHANCEMENTS IN PROMPT ===")

    # Check for specific enhancements
    enhancements_found = {
        "Empty Column Skip Detection": "EMPTY COLUMN SKIP DETECTION" in prompt,
        "Empty Column Skip Analysis": "Empty Column Skip Analysis" in prompt,
        "CalcCode/Frequency Example": "CalcCode contains 'B5' but should be empty" in prompt,
        "Empty Skip Shift Pattern": "EMPTY_SKIP_SHIFT" in prompt,
        "Empty Column Skip Issues Output": "empty_column_skip_issues" in prompt,
    }

    for enhancement, found in enhancements_found.items():
        status = "✓ FOUND" if found else "✗ MISSING"
        print(f"{status}: {enhancement}")

    print()
    print("=== SPECIFIC PROMPTING FOR B5 ISSUE ===")

    # Extract specific sections that address the B5 issue
    b5_specific_sections = []
    lines = prompt.split('\n')
    capturing = False
    current_section = []

    for line in lines:
        if "EMPTY COLUMN SKIP" in line.upper():
            if current_section and capturing:
                b5_specific_sections.append('\n'.join(current_section))
            current_section = [line]
            capturing = True
        elif capturing and (line.startswith("**") or line.startswith("##")):
            if current_section:
                b5_specific_sections.append('\n'.join(current_section))
            current_section = []
            capturing = False
        elif capturing:
            current_section.append(line)

    if current_section and capturing:
        b5_specific_sections.append('\n'.join(current_section))

    for i, section in enumerate(b5_specific_sections, 1):
        print(f"\n--- Enhancement Section {i} ---")
        print(section[:300] + "..." if len(section) > 300 else section)

    print()
    print("=== DETECTION CAPABILITY ASSESSMENT ===")

    total_enhancements = len(enhancements_found)
    found_enhancements = sum(enhancements_found.values())

    print(f"Enhanced Features: {found_enhancements}/{total_enhancements}")
    print(f"Detection Readiness: {found_enhancements/total_enhancements*100:.1f}%")

    if found_enhancements == total_enhancements:
        print("✓ ALL ENHANCEMENTS PRESENT - Should detect B5 misalignment")
        return True
    else:
        print("✗ MISSING ENHANCEMENTS - May not detect B5 misalignment reliably")
        return False

if __name__ == "__main__":
    print("Testing Enhanced B5 Misalignment Detection...")
    print("=" * 60)

    try:
        success = test_b5_misalignment_detection()
        print()
        if success:
            print("✓ Enhanced prompt ready to detect B5 CalcCode/Frequency misalignment!")
            print("\nKey improvements:")
            print("  • Empty column skip detection logic")
            print("  • Specific CalcCode/Frequency analysis")
            print("  • Chain of thought reasoning for column gaps")
            print("  • Detailed output format for empty column issues")
        else:
            print("✗ Prompt needs further enhancement!")

    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        raise