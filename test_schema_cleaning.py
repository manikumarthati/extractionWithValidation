#!/usr/bin/env python3
"""
Test script to verify schema cleaning integration works end-to-end
"""

import json
from services.schema_text_extractor import SchemaTextExtractor

def test_schema_cleaning():
    """Test that schema cleaning removes hints and metadata from output"""

    # Sample schema with descriptions and metadata (hints for LLM)
    test_schema = {
        "documentSchema": {
            "entityTypes": [
                {
                    "name": "custom_extraction_document_type",
                    "properties": [
                        {
                            "name": "Employee_Master",
                            "valueType": "Employee_Master",
                            "description": "You are an expert data extraction system for Payroll documents. Extract employee information carefully.",
                            "method": "EXTRACT",
                            "propertyMetadata": {"hint": "focus on name and ID"}
                        },
                        {
                            "name": "Company_Name",
                            "valueType": "string",
                            "description": "Company name from header section",
                            "method": "EXTRACT"
                        }
                    ]
                }
            ]
        }
    }

    # Initialize extractor (without API key for testing structure only)
    extractor = SchemaTextExtractor("")

    # Test clean schema extraction
    clean_schema = extractor._extract_clean_schema_structure(test_schema)
    print("[OK] Clean Schema Structure:")
    print(json.dumps(clean_schema, indent=2))

    # Test clean output format
    sample_data = {"Employee_Master": {"name": "John Doe"}, "Company_Name": "ACME Corp"}
    clean_output = extractor._create_clean_output_format(sample_data, test_schema, "test_method")

    print("\n[OK] Clean Output Format:")
    print(json.dumps(clean_output, indent=2))

    # Verify no hints/descriptions in output
    output_str = json.dumps(clean_output)

    # Check that problematic content is NOT present
    problematic_content = [
        "You are an expert data extraction system",
        '"description"',
        '"method": "EXTRACT"',
        "propertyMetadata",
        '"EXTRACT"'
    ]

    issues_found = []
    for content in problematic_content:
        if content in output_str:
            issues_found.append(content)

    if issues_found:
        print(f"\n[ERROR] Found problematic content in output: {issues_found}")
        return False
    else:
        print(f"\n[OK] No problematic content found in output")

    # Verify essential structure is preserved
    expected_keys = ["success", "extracted_data", "extraction_method", "schema_structure"]
    missing_keys = [key for key in expected_keys if key not in clean_output]

    if missing_keys:
        print(f"\n[ERROR] Missing essential keys: {missing_keys}")
        return False
    else:
        print(f"\n[OK] All essential keys present")

    return True

if __name__ == "__main__":
    print("Testing Schema Cleaning Integration...")
    success = test_schema_cleaning()

    if success:
        print("\n[SUCCESS] All tests passed! Schema cleaning is properly integrated.")
    else:
        print("\n[FAILED] Tests failed! Schema cleaning needs fixes.")