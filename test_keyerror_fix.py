#!/usr/bin/env python3
"""
Test that the KeyError fix works properly
"""

import json
from services.schema_text_extractor import SchemaTextExtractor

def test_output_structure():
    """Test that the new output structure is consistent"""

    # Sample schema
    test_schema = {
        "documentSchema": {
            "entityTypes": [
                {
                    "name": "document",
                    "properties": [
                        {
                            "name": "Employee_Name",
                            "valueType": "string"
                        },
                        {
                            "name": "Company",
                            "valueType": "string"
                        }
                    ]
                }
            ]
        }
    }

    # Initialize extractor
    extractor = SchemaTextExtractor("")

    # Test clean output format structure
    sample_data = {"Employee_Name": "John Doe", "Company": "ACME Corp"}
    clean_output = extractor._create_clean_output_format(sample_data, test_schema, "test_method")

    print("[TEST] Output Structure Check:")
    print(json.dumps(clean_output, indent=2))

    # Check for expected keys
    expected_keys = ["success", "extracted_data", "extraction_method", "schema_structure"]

    missing_keys = []
    for key in expected_keys:
        if key not in clean_output:
            missing_keys.append(key)

    # Check for old keys that should NOT be present
    old_keys = ["final_data", "schema_used"]
    found_old_keys = []
    for key in old_keys:
        if key in clean_output:
            found_old_keys.append(key)

    print(f"\n[RESULT] Expected keys present: {len(missing_keys) == 0}")
    if missing_keys:
        print(f"[ERROR] Missing keys: {missing_keys}")

    print(f"[RESULT] Old keys removed: {len(found_old_keys) == 0}")
    if found_old_keys:
        print(f"[ERROR] Found old keys: {found_old_keys}")

    # Verify extracted_data contains the actual data
    if "extracted_data" in clean_output:
        extracted = clean_output["extracted_data"]
        print(f"[RESULT] extracted_data contains data: {len(extracted) > 0}")
        print(f"[INFO] extracted_data keys: {list(extracted.keys())}")
    else:
        print("[ERROR] extracted_data key missing!")

    return len(missing_keys) == 0 and len(found_old_keys) == 0

if __name__ == "__main__":
    print("Testing KeyError Fix...")
    success = test_output_structure()

    if success:
        print("\n[SUCCESS] KeyError fix working properly!")
        print("Apps should now access result['extracted_data'] instead of result['final_data']")
    else:
        print("\n[FAILED] KeyError fix needs more work!")