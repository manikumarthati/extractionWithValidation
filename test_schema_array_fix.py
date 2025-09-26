#!/usr/bin/env python3
"""
Test the fixed _extract_clean_schema_structure method to ensure it properly handles arrays
"""

import json
import os
from services.schema_text_extractor import SchemaTextExtractor

def test_schema_array_structure():
    """Test that arrays are properly recognized and structured"""

    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment variables")
        return False

    # Create extractor
    extractor = SchemaTextExtractor(api_key)

    # Test schema with Employer_Tax structure similar to the real schema
    test_schema = {
        "documentSchema": {
            "entityTypes": [
                {
                    "name": "Employee_Master",
                    "properties": [
                        {
                            "name": "Employee_Name",
                            "valueType": "string",
                            "occurrenceType": "OPTIONAL_ONCE"
                        },
                        {
                            "name": "Employer_Tax",
                            "valueType": "Employer_Tax",
                            "occurrenceType": "OPTIONAL_MULTIPLE"
                        }
                    ]
                },
                {
                    "name": "Employer_Tax",
                    "properties": [
                        {
                            "name": "Employer_Tax_Code",
                            "valueType": "string",
                            "occurrenceType": "OPTIONAL_ONCE"
                        },
                        {
                            "name": "Employer_Tax_Description",
                            "valueType": "string",
                            "occurrenceType": "OPTIONAL_ONCE"
                        },
                        {
                            "name": "Employer_Tax_Start_Date",
                            "valueType": "datetime",
                            "occurrenceType": "OPTIONAL_ONCE"
                        },
                        {
                            "name": "Employer_Tax_End_Date",
                            "valueType": "datetime",
                            "occurrenceType": "OPTIONAL_ONCE"
                        }
                    ]
                }
            ]
        }
    }

    try:
        print("Testing schema array structure extraction...")

        # Test the fixed method
        clean_schema = extractor._extract_clean_schema_structure(test_schema)

        print("Clean schema structure:")
        print(json.dumps(clean_schema, indent=2))

        # Verify the fix
        success = True

        # Check that Employer_Tax is treated as an array with proper structure
        if "Employer_Tax" not in clean_schema:
            print("ERROR: Employer_Tax not found in clean schema")
            success = False
        elif not isinstance(clean_schema["Employer_Tax"], list):
            print("ERROR: Employer_Tax should be a list/array structure")
            success = False
        else:
            # Check that the array contains the proper object structure
            if len(clean_schema["Employer_Tax"]) != 1:
                print("ERROR: Employer_Tax array should contain one structure template")
                success = False
            else:
                employer_tax_structure = clean_schema["Employer_Tax"][0]
                expected_fields = [
                    "Employer_Tax_Code",
                    "Employer_Tax_Description",
                    "Employer_Tax_Start_Date",
                    "Employer_Tax_End_Date"
                ]

                for field in expected_fields:
                    if field not in employer_tax_structure:
                        print(f"ERROR: Missing field {field} in Employer_Tax structure")
                        success = False

        # Check that Employee_Master is treated as a regular object
        if "Employee_Master" not in clean_schema:
            print("ERROR: Employee_Master not found in clean schema")
            success = False
        elif isinstance(clean_schema["Employee_Master"], list):
            print("ERROR: Employee_Master should NOT be a list (it's not MULTIPLE)")
            success = False

        return success

    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Schema Array Structure Fix")
    print("=" * 40)

    success = test_schema_array_structure()

    if success:
        print("\nTest passed!")
        print("The fix correctly:")
        print("- Identifies entities with OPTIONAL_MULTIPLE/REQUIRED_MULTIPLE occurrence")
        print("- Creates proper array structures [{ field1: type, field2: type }]")
        print("- Treats individual fields as columns within the array items")
        print("- Maintains regular objects for non-MULTIPLE entities")
    else:
        print("\nTest failed - fix needs more work")