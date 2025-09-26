#!/usr/bin/env python3
"""
Test the enhanced extraction prompt with blank fields and complete text handling
"""

import json
import os
from services.schema_text_extractor import SchemaTextExtractor

def test_enhanced_extraction(config_name='current'):
    """Test enhanced extraction with blank fields and partial text scenarios"""

    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment variables")
        return False

    # Create extractor
    extractor = SchemaTextExtractor(api_key)

    # Test schema focused on the issues we're addressing
    test_schema = {
        "documentSchema": {
            "entityTypes": [
                {
                    "name": "employee_test",
                    "properties": [
                        {
                            "name": "Employee_Name",
                            "valueType": "string",
                            "occurrenceType": "OPTIONAL_ONCE"
                        },
                        {
                            "name": "Position",
                            "valueType": "string",
                            "occurrenceType": "OPTIONAL_ONCE"
                        },
                        {
                            "name": "Emp_Type",
                            "valueType": "string",
                            "occurrenceType": "OPTIONAL_ONCE"
                        },
                        {
                            "name": "Title",
                            "valueType": "string",
                            "occurrenceType": "OPTIONAL_ONCE"
                        },
                        {
                            "name": "Employer_Tax_Records",
                            "valueType": "Employer_Tax_Record",
                            "occurrenceType": "OPTIONAL_MULTIPLE"
                        }
                    ]
                },
                {
                    "name": "Employer_Tax_Record",
                    "properties": [
                        {
                            "name": "Tax_Code",
                            "valueType": "string",
                            "occurrenceType": "OPTIONAL_ONCE"
                        },
                        {
                            "name": "Tax_Description",
                            "valueType": "string",
                            "occurrenceType": "OPTIONAL_ONCE"
                        },
                        {
                            "name": "Effective_Dates",
                            "valueType": "string",
                            "occurrenceType": "OPTIONAL_ONCE"
                        }
                    ]
                }
            ]
        }
    }

    # Simulate raw text that contains the scenarios we're testing
    mock_raw_text = """
    Employee Profile Velorynt Labs
    Company (37546)
    Period: 12/17/2024 to 12/26/2024 Page 65

    Caroline Jones
    Stream Apt. 219 Emp Id 4632 Status A Emp Type Home # 509-121-3247
    Riverton, UT SSN 088-39-6286 Position Statutory 0.00 Work #
    47589 DOB 12/26/2001(22) Title Seasonal 0.00 Ext.

    EmployerTax Effective Dates Default
    MED-R Medicare - Employer 04/28/2023 to 12/31/2100
    SS-R OASDI - Employer 04/28/2023 to 12/31/2100
    FUTA Fed Unemployment 04/28/2023 to 12/31/2100
    MNAST Minnesota Federal Loan 04/28/2023 Assessment to 12/31/2100
    MNDW Workforce Enhancement Fee 04/28/2023 to 12/31/2100
    MNSUI Minnesota SUI 04/28/2023 to 12/31/2100
    """

    try:
        print("Testing enhanced extraction with blank fields and complete text...")
        print("Mock text includes:")
        print("- Employee_Name: Caroline Jones (should be extracted)")
        print("- Position: (blank field after Position label)")
        print("- Emp_Type: (blank field after Emp Type label)")
        print("- Title: (blank field after Title label)")
        print("- MNDW: 'Workforce Enhancement Fee' (complete text)")
        print()

        # Test the enhanced prompt
        extraction_result = extractor.extract_with_schema_from_text(mock_raw_text, test_schema)

        if extraction_result["success"]:
            extracted_data = extraction_result["extracted_data"]
            print("Extraction Results:")
            print(json.dumps(extracted_data, indent=2))

            # Test blank field handling
            success = True

            # Check blank fields are extracted as empty strings, not null
            blank_fields = ["Position", "Emp_Type", "Title"]
            for field in blank_fields:
                if field in extracted_data:
                    if extracted_data[field] == "":
                        print(f"[PASS] {field}: Correctly extracted as empty string")
                    elif extracted_data[field] is None:
                        print(f"[FAIL] {field}: Incorrectly extracted as null instead of empty string")
                        success = False
                    else:
                        print(f"[INFO] {field}: Extracted as '{extracted_data[field]}' (unexpected value)")
                else:
                    print(f"[FAIL] {field}: Missing from extraction (should be empty string)")
                    success = False

            # Check complete text extraction
            if "Employer_Tax_Records" in extracted_data:
                for record in extracted_data["Employer_Tax_Records"]:
                    if record.get("Tax_Code") == "MNDW":
                        description = record.get("Tax_Description", "")
                        if "Workforce Enhancement Fee" in description:
                            print(f"[PASS] Complete text: '{description}' (complete version extracted)")
                        else:
                            print(f"[FAIL] Incomplete text: '{description}' (should be 'Workforce Enhancement Fee')")
                            success = False
                        break

            return success

        else:
            print(f"Extraction failed: {extraction_result.get('error')}")
            return False

    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Enhanced Extraction Prompt")
    print("=" * 40)

    success = test_enhanced_extraction()

    if success:
        print("\n[SUCCESS] Enhanced extraction test passed!")
        print("The prompt correctly handles:")
        print("- Blank fields as empty strings (not null)")
        print("- Complete text extraction from raw text")
    else:
        print("\n[FAILED] Enhanced extraction test failed")
        print("May need to adjust prompt or try Option 3 (hybrid approach)")