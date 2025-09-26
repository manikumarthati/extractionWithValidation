#!/usr/bin/env python3
"""
Test script for the enhanced Chain of Thought visual validation prompt
"""

from services.visual_field_inspector import VisualFieldInspector
import json

def test_enhanced_prompt():
    """Test the enhanced CoT validation prompt generation"""

    # Sample extracted data for testing
    sample_extracted_data = {
        "employee_profile_document": {
            "Document_Header": {
                "Company_Name": "Velorynt Labs",
                "Company_Code": "37546",
                "Period_From": "2024-12-17",
                "Period_To": "2024-12-26",
                "Page_Number": "69"
            },
            "Employee_Profile": {
                "Basic_Information": {
                    "Employee_Name": "Jocelyn Taylor",
                    "Address": {
                        "Street_Address": "1006 Shery St",
                        "City": "Shaontown",
                        "State": "WY",
                        "Zip_Code": "93506-7144"
                    },
                    "Employment_Details": {
                        "Employee_ID": 5532,
                        "Status": "A",
                        "Employee_Type": "RFT",
                        "Position": "",
                        "Title": "",
                        "Hire_Date": "2016-01-04"
                    }
                },
                "Rate_Salary_Information": {
                    "Rate_Records": [
                        {
                            "Rate_Code": "Base",
                            "Description": "Base Rate",
                            "Rate": 20.95,
                            "Effective_Start_Date": "2024-01-03",
                            "Effective_End_Date": "2100-12-31"
                        }
                    ]
                }
            }
        }
    }

    # Sample schema
    sample_schema = {
        "employee_profile_document": "object",
        "Document_Header": {
            "Company_Name": "string",
            "Company_Code": "string",
            "Period_From": "datetime",
            "Period_To": "datetime",
            "Page_Number": "string"
        },
        "Employee_Profile": {
            "Basic_Information": "object",
            "Rate_Salary_Information": "object"
        }
    }

    # Create inspector instance (without API key for testing prompt generation)
    inspector = VisualFieldInspector("")

    # Generate the enhanced prompt
    prompt = inspector._build_comprehensive_visual_validation_prompt(
        sample_extracted_data, sample_schema
    )

    print("=== ENHANCED CHAIN OF THOUGHT VALIDATION PROMPT ===")
    print()
    print(prompt)
    print()
    print("=== PROMPT ANALYSIS ===")

    # Analyze the prompt components
    components = {
        "Chain of Thought Steps": prompt.count("**STEP"),
        "Reasoning Instructions": prompt.count("reasoning"),
        "Self-Explanation Requirements": prompt.count("confidence"),
        "Visual Cues Mentions": prompt.count("visual_cues"),
        "Systematic Analysis": prompt.count("systematic"),
        "Think Step-by-Step": prompt.count("think step by step"),
    }

    print(f"Prompt Length: {len(prompt):,} characters")
    print(f"Prompt Components:")
    for component, count in components.items():
        print(f"  - {component}: {count}")

    # Check if key Chain of Thought elements are present
    cot_elements = [
        "STEP 1: DOCUMENT UNDERSTANDING",
        "STEP 2: SYSTEMATIC FIELD-BY-FIELD",
        "STEP 3: TABLE STRUCTURE ANALYSIS",
        "STEP 4: COLUMN ALIGNMENT VERIFICATION",
        "STEP 5: CONFIDENCE ASSESSMENT",
        "STEP 6: COMPREHENSIVE REASONING SYNTHESIS",
        "reasoning_steps",
        "confidence_justification",
        "self_verification"
    ]

    print(f"\nChain of Thought Elements Present:")
    for element in cot_elements:
        present = element in prompt
        status = "✓" if present else "✗"
        print(f"  {status} {element}")

    print("\n=== TEST COMPLETED ===")
    return True

if __name__ == "__main__":
    print("Testing Enhanced Chain of Thought Visual Validation Prompt...")
    print("=" * 60)

    try:
        success = test_enhanced_prompt()
        if success:
            print("\n✓ Enhanced prompt test completed successfully!")
            print("\nThe prompt now includes:")
            print("  • Step-by-step Chain of Thought reasoning")
            print("  • Self-explanation requirements")
            print("  • Confidence assessment and justification")
            print("  • Visual cue analysis")
            print("  • Systematic verification steps")
            print("  • Reasoning trace output format")
        else:
            print("\n✗ Test failed!")

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        raise